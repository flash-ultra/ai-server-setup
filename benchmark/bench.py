#!/usr/bin/env python3
"""
Serving benchmark — fixed protocol, comparable across models and engines.

The point of this script is that the numbers it produces can be compared. Every
parameter that affects throughput is pinned here rather than passed on the command
line: prompt text, concurrency levels, max_tokens, measurement window, warmup, and how
tokens are counted. Change any of them and you are producing a different series, so
bump PROTOCOL below and say so in the scenario document.

Usage:
    ./bench.py --url http://localhost:8000 --model <served-name> --scenario concurrent
    ./bench.py --url ... --model ... --scenario single
    ./bench.py --url ... --model ... --scenario reasoning
    ./bench.py --url ... --model ... --scenario longctx

Requires only the standard library. Targets any OpenAI-compatible /v1/chat/completions.
"""

import argparse, json, random, statistics, subprocess, sys, threading, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PROTOCOL = "v1"

# ---------------------------------------------------------------- fixed parameters
DURATION_S = 40           # measurement window per level
WARMUP_REQUESTS = 3       # per level, discarded — first request after start is slow
MAX_TOKENS = 512          # must leave room for reasoning models; see protocol README
LEVELS = [1, 8, 16, 32, 64, 128, 256]
GPU_POLL_S = 1.0
CHAT_TEMPLATE_KWARGS = None   # set from --chat-template-kwargs; applies to every request

# The prompt is pinned, not just its length. With speculative decoding, draft
# acceptance depends on how predictable the text is — same token count, different
# content, different throughput. Kept verbatim across models so series stay comparable.
FILLER = ("The company operates a distributed server infrastructure across several sites "
          "and requires a structured evaluation of its operational data. ")
PROMPT = "Summarise the following report in three sentences.\n\n" + FILLER * 60

# Mixed traffic: five request shapes, drawn at random per request. Approximates agent
# traffic, which is never uniform. Weights are equal on purpose — no claim that this
# matches any particular production mix.
MIX = [
    "What is the difference between an index and a primary key?",
    ("Review this code for defects:\n\ndef parse(rows):\n    out = {}\n    for r in rows:\n"
     "        k, v = r.split(chr(61))\n        out[k] = int(v)\n    return out\n\n"
     "What happens with empty lines, or values that are not numbers?"),
    "Analyse the following report and name the three largest risks.\n\n" + FILLER * 180,
    ("You have access to the function query_metrics(host, from, to). A user asks for the "
     "CPU utilisation of web-03 over the last 24 hours. Formulate the call."),
    "Explain the trade-offs of event sourcing for an order management system.\n\n" + FILLER * 20,
]

# Long-context needles: one early, one mid, one late. The mid needle is the actual
# test — models that only attend to the edges recover the outer two and miss it.
NEEDLES = [
    (0.10, "IMPORTANT: The verification code for site North is XR-4471.", "XR-4471"),
    (0.50, "IMPORTANT: The verification code for site Central is QT-8829.", "QT-8829"),
    (0.90, "IMPORTANT: The verification code for site South is ZB-1503.", "ZB-1503"),
]
NEEDLE_QUESTION = ("\n\nQuestion: three verification codes are hidden in the text above "
                   "(North, Central, South). Name all three exactly. Answer briefly.")


# ---------------------------------------------------------------- gpu sampling
class GpuSampler:
    def __init__(self):
        self.samples, self._stop, self._t = [], False, None

    def __enter__(self):
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()
        return self

    def _loop(self):
        while not self._stop:
            try:
                out = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5).stdout.split()
                if out:
                    self.samples.append([int(x) for x in out])
            except Exception:
                pass
            time.sleep(GPU_POLL_S)

    def __exit__(self, *a):
        self._stop = True
        if self._t:
            self._t.join(timeout=3)

    def per_card(self):
        if not self.samples:
            return []
        n = len(self.samples[0])
        return [round(statistics.mean(s[i] for s in self.samples if len(s) > i)) for i in range(n)]


# ---------------------------------------------------------------- request
def request(url, model, prompt, extra=None, max_tokens=MAX_TOKENS, timeout=3600, stream=False):
    """One completion. Returns usage-based metrics, or None on failure."""
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": 1.0, "top_p": 1.0}
    if CHAT_TEMPLATE_KWARGS:
        body["chat_template_kwargs"] = dict(CHAT_TEMPLATE_KWARGS)
    if extra:
        body.update(extra)
    if stream:
        body["stream"] = True
    req = urllib.request.Request(url + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        if stream:
            ttft, ntok, text = None, 0, ""
            with urllib.request.urlopen(req, timeout=timeout) as r:
                for line in r:
                    if not line.startswith(b"data: "):
                        continue
                    chunk = line[6:].strip()
                    if chunk == b"[DONE]":
                        break
                    try:
                        d = json.loads(chunk)
                    except Exception:
                        continue
                    delta = d["choices"][0].get("delta", {}) or {}
                    piece = delta.get("content") or delta.get("reasoning_content") or ""
                    if piece:
                        if ttft is None:
                            ttft = time.time() - t0
                        ntok += 1
                        if delta.get("content"):
                            text += delta["content"]
            return {"lat": time.time() - t0, "ttft": ttft, "stream_tokens": ntok, "text": text}
        d = json.load(urllib.request.urlopen(req, timeout=timeout))
    except Exception:
        return None
    u = d.get("usage", {}) or {}
    det = u.get("completion_tokens_details") or {}
    msg = d["choices"][0]["message"]
    return {"lat": time.time() - t0,
            "out": u.get("completion_tokens", 0),
            "inp": u.get("prompt_tokens", 0),
            "reasoning": det.get("reasoning_tokens", u.get("reasoning_tokens", 0)),
            "chars": len((msg.get("content") or "").strip()),
            "text": msg.get("content") or ""}


def measure(url, model, level, picker, extra=None, duration=DURATION_S):
    """Saturate `level` workers for `duration`, after a warmup that is discarded."""
    for _ in range(WARMUP_REQUESTS):
        request(url, model, picker(random.Random(0)), extra, timeout=900)

    results, deadline = [], time.time() + duration
    with GpuSampler() as gpu:
        def worker(seed):
            rnd = random.Random(seed)
            while time.time() < deadline:
                r = request(url, model, picker(rnd), extra, timeout=900)
                if r:
                    results.append(r)
        with ThreadPoolExecutor(max_workers=level) as ex:
            for f in [ex.submit(worker, i) for i in range(level)]:
                f.result()
        cards = gpu.per_card()

    if not results:
        return None
    out = sum(r["out"] for r in results)
    lats = sorted(r["lat"] for r in results)
    return {"n": len(results), "answers_s": len(results) / duration,
            "out_s": out / duration, "total_s": (out + sum(r["inp"] for r in results)) / duration,
            "tokens_per_answer": out / len(results),
            "reasoning_pct": 100 * sum(r["reasoning"] for r in results) / out if out else 0,
            "chars_per_answer": sum(r["chars"] for r in results) / len(results),
            "p50": lats[len(lats) // 2],
            "p95": lats[int(len(lats) * 0.95) - 1] if len(lats) > 1 else lats[0],
            "gpu": cards}


def fmt_gpu(cards):
    return " · ".join(f"{c} %" for c in cards) if cards else "—"


# ---------------------------------------------------------------- scenarios
def scenario_concurrent(url, model, levels=None):
    print(f"| Concurrent | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 | GPU |")
    print(f"|---|---|---|---|---|---|---|")
    for lvl in (levels or LEVELS):
        r = measure(url, model, lvl, lambda _: PROMPT)
        if not r:
            print(f"| {lvl} | failed | | | | | |"); continue
        print(f"| {lvl} | {r['answers_s']:.2f} | {r['out_s']:.1f} | {r['total_s']:.1f} | "
              f"{r['p50']:.2f} s | {r['p95']:.2f} s | {fmt_gpu(r['gpu'])} |")
        sys.stdout.flush()

    print("\n**Prompt mix at concurrency 32**\n")
    print("| Traffic | Answers/s | Output tok/s | Total tok/s | Latency p50 | p95 |")
    print("|---|---|---|---|---|---|")
    for label, picker in [("uniform", lambda _: PROMPT),
                          ("mixed", lambda rnd: rnd.choice(MIX))]:
        r = measure(url, model, 32, picker)
        if r:
            print(f"| {label} | {r['answers_s']:.2f} | {r['out_s']:.1f} | {r['total_s']:.1f} | "
                  f"{r['p50']:.2f} s | {r['p95']:.2f} s |")


def scenario_single(url, model):
    r = measure(url, model, 1, lambda _: PROMPT)
    if not r:
        print("failed"); return
    print("| Metric | Value |")
    print("|---|---|")
    print(f"| Output | {r['out_s']:.1f} tok/s |")
    print(f"| Total (incl. reasoning) | {r['total_s']:.1f} tok/s |")
    print(f"| Requests | {r['answers_s']:.2f} req/s |")
    print(f"| Latency p50 | {r['p50']:.2f} s |")
    print(f"| Tokens per answer | {r['tokens_per_answer']:.0f} ({r['reasoning_pct']:.0f} % reasoning) |")
    print(f"| GPU utilisation | {fmt_gpu(r['gpu'])} |")


def scenario_reasoning(url, model, thinking_key="thinking"):
    # The key that turns thinking off is a property of the checkpoint's chat template,
    # not of the protocol. DeepSeek-V4 uses "thinking", Gemma-4 uses "enable_thinking",
    # and a template that carries neither cannot be switched at all — an unknown key is
    # accepted and silently ignored, which reads as "no effect" rather than "no switch".
    # Verify against the model before trusting a thinking-off row.
    variants = [("default", None),
                ("reasoning_effort=low", {"reasoning_effort": "low"}),
                (f"thinking off ({thinking_key})",
                 {"chat_template_kwargs": {thinking_key: False}})]
    print("| Concurrency | Variant | Answers/s | Output tok/s | Tokens/answer | Reasoning | Chars/answer | Latency p50 | GPU |")
    print("|---|---|---|---|---|---|---|---|---|")
    for lvl in (8, 32):
        for label, extra in variants:
            r = measure(url, model, lvl, lambda _: PROMPT, extra)
            if not r:
                print(f"| {lvl} | {label} | failed | | | | | | |"); continue
            print(f"| {lvl} | {label} | {r['answers_s']:.2f} | {r['out_s']:.1f} | "
                  f"{r['tokens_per_answer']:.0f} | {r['reasoning_pct']:.0f} % | "
                  f"{r['chars_per_answer']:.0f} | {r['p50']:.2f} s | {fmt_gpu(r['gpu'])} |")
            sys.stdout.flush()


def scenario_longctx(url, model, target_tokens=960000):
    # Calibrate against the server's own tokeniser rather than guessing.
    base = request(url, model, "hi", max_tokens=1)
    probe = request(url, model, FILLER * 200, max_tokens=1)
    if not base or not probe:
        print("calibration failed"); return
    per_sentence = (probe["inp"] - base["inp"]) / 200
    n = int(target_tokens / per_sentence)
    print(f"calibration: {per_sentence:.2f} tokens/sentence → {n} sentences\n")

    at = {int(n * pos): text for pos, text, _ in NEEDLES}
    parts = []
    for i in range(n):
        if i in at:
            parts.append(at[i] + " ")
        parts.append(FILLER)
    prompt = "".join(parts) + NEEDLE_QUESTION
    print(f"prompt: {len(prompt)/1e6:.2f} MB, needles at 10/50/90 %\n")

    with GpuSampler() as gpu:
        r = request(url, model, prompt, max_tokens=600, stream=True)
        cards = gpu.per_card()
    if not r:
        print("request failed"); return

    found = [code for _, _, code in NEEDLES if code in r["text"]]
    print("| Metric | Value |")
    print("|---|---|")
    print(f"| Prefill (TTFT) | {r['ttft']:.1f} s |")
    print(f"| Prefill throughput | {target_tokens/r['ttft']:.0f} tok/s |")
    print(f"| Total duration | {r['lat']:.1f} s |")
    print(f"| GPU utilisation | {fmt_gpu(cards)} |")
    print(f"| Needles recovered | **{len(found)} of {len(NEEDLES)}** {found} |")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Serving benchmark, protocol " + PROTOCOL)
    ap.add_argument("--url", required=True, help="base URL, e.g. http://localhost:8000")
    ap.add_argument("--model", required=True, help="served model name")
    ap.add_argument("--scenario", required=True,
                    choices=["concurrent", "single", "reasoning", "longctx"])
    ap.add_argument("--target-tokens", type=int, default=960000,
                    help="longctx only: prompt size to build (default 960000)")
    ap.add_argument("--chat-template-kwargs", default=None,
                    help="JSON object sent as chat_template_kwargs on EVERY request, e.g. "
                         "{\"enable_thinking\": false}. Engines differ in what they default "
                         "to for the same checkpoint — SGLang served Gemma-4 with thinking "
                         "off where llama.cpp had it on — so a cross-engine comparison has "
                         "to pin the state rather than inherit it")
    ap.add_argument("--thinking-key", default="thinking",
                    help="reasoning only: chat_template_kwargs key that disables thinking. "
                         "DeepSeek-V4 uses the default; Gemma-4 needs enable_thinking. An "
                         "unknown key is ignored silently, so check the model first")
    ap.add_argument("--levels", type=lambda s: [int(x) for x in s.split(",")],
                    help="concurrent only: override the protocol levels, e.g. 256,384,512. "
                         "Every other parameter stays at its pinned value; the deviation is "
                         "recorded in the output header and must be stated in the scenario's "
                         "Method section")
    a = ap.parse_args()

    global CHAT_TEMPLATE_KWARGS
    if a.chat_template_kwargs:
        CHAT_TEMPLATE_KWARGS = json.loads(a.chat_template_kwargs)

    dev = ""
    if CHAT_TEMPLATE_KWARGS:
        dev += " · chat_template_kwargs: " + json.dumps(CHAT_TEMPLATE_KWARGS)
    if a.scenario == "reasoning" and a.thinking_key != "thinking":
        dev += f" · thinking key: {a.thinking_key}"
    if a.levels and a.levels != LEVELS:
        dev = (f" · DEVIATION: levels {','.join(map(str, a.levels))} instead of the pinned "
               f"{','.join(map(str, LEVELS))}")
    print(f"<!-- protocol {PROTOCOL} · max_tokens {MAX_TOKENS} · {DURATION_S} s/level · "
          f"{WARMUP_REQUESTS} warmup requests discarded · counted via usage fields{dev} -->\n")
    {"concurrent": lambda: scenario_concurrent(a.url, a.model, a.levels),
     "single": lambda: scenario_single(a.url, a.model),
     "reasoning": lambda: scenario_reasoning(a.url, a.model, a.thinking_key),
     "longctx": lambda: scenario_longctx(a.url, a.model, a.target_tokens)}[a.scenario]()


if __name__ == "__main__":
    main()
