#!/usr/bin/env python3
"""Embedding load against one or more OpenAI-compatible servers (vLLM --runner pooling).
Throughput over the real run time: tokens of all responses / (last response - start).
  embbench.py --urls http://127.0.0.1:8001[,..] --scenario ingest|query|long [--chunk 512 --batch 32 --levels 1,4,16,64]
Worker i talks to server i % n; with four servers each gets C/4 connections."""
import argparse, asyncio, json, random, statistics as st, sys, time
import httpx
sys.path.insert(0, __import__("os").path.dirname(__file__))
from embcommon import Client, text_pool, load_task, fmt_query

ap = argparse.ArgumentParser()
ap.add_argument("--urls", required=True); ap.add_argument("--model", default="cyberlink")
ap.add_argument("--api", default="openai"); ap.add_argument("--style", default="bge")
ap.add_argument("--scenario", default="ingest")
ap.add_argument("--chunk", type=int, default=512); ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--levels", default="1,4,16,64"); ap.add_argument("--duration", type=float, default=40)
ap.add_argument("--long", default="2048,8192,32768"); ap.add_argument("--reps", type=int, default=3)
ap.add_argument("--nq", type=int, default=200); ap.add_argument("--truncate", type=int, default=None)
a = ap.parse_args()
URLS = a.urls.split(","); CL = Client(URLS, a.model, a.api, a.truncate)
POOL = text_pool(); RNG = random.Random(11)

def ratio():
    """Tokens per character for this model, measured with /tokenize on 40k characters."""
    s = POOL[100000:140000]
    try:
        r = httpx.post(f"{URLS[0]}/tokenize", json={"model": a.model, "prompt": s}, timeout=120); r.raise_for_status()
        return r.json()["count"] / len(s)
    except Exception as e:
        print(f"<!-- /tokenize failed ({e}); assuming 0.27 tokens/char -->"); return 0.27
TPC = ratio()

def chunk(ntok):
    n = int(ntok / TPC); o = RNG.randrange(0, len(POOL) - n - 1)
    o = POOL.find(" ", o) + 1
    return POOL[o:o + n]

def pct(xs, p):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(p / 100 * len(xs)))] if xs else 0

async def level(C, make, dur):
    res = []; t0 = time.perf_counter(); stop = t0 + dur
    async def worker(i):
        url = URLS[i % len(URLS)]
        async with httpx.AsyncClient(timeout=3600, limits=httpx.Limits(max_connections=4)) as ac:
            while time.perf_counter() < stop:
                texts = make()
                v, u, lat = await CL.embed(ac, url, texts)
                res.append((time.perf_counter(), lat, u, len(v)))
    await asyncio.gather(*[worker(i) for i in range(C)])
    wall = max(r[0] for r in res) - t0
    tok = sum(r[2] for r in res); items = sum(r[3] for r in res); lats = [r[1] for r in res]
    return dict(C=C, wall=wall, req=len(res), items=items, tok=tok, tps=tok / wall, ips=items / wall,
                p50=st.median(lats), p95=pct(lats, 95), tpi=tok / max(items, 1))

async def warm():
    async with httpx.AsyncClient(timeout=3600) as ac:
        await asyncio.gather(*[CL.embed(ac, u, [chunk(a.chunk) for _ in range(4)]) for u in URLS])

async def main():
    await warm()
    print(f"<!-- urls={len(URLS)} model={a.model} scenario={a.scenario} tok/char={TPC:.3f} -->\n")
    if a.scenario == "ingest":
        print(f"### Ingest: {a.batch} chunks of ~{a.chunk} tokens per request\n")
        print("| Clients | Requests | Chunks/s | Input tok/s | Tokens/chunk | p50 request | p95 request | Wall |")
        print("|---:|---:|---:|---:|---:|---:|---:|---:|")
        for C in map(int, a.levels.split(",")):
            r = await level(C, lambda: [chunk(a.chunk) for _ in range(a.batch)], a.duration)
            print(f"| {C} | {r['req']} | {r['ips']:,.0f} | {r['tps']:,.0f} | {r['tpi']:.0f} | {r['p50']:.3f} s | {r['p95']:.3f} s | {r['wall']:.1f} s |", flush=True)
    elif a.scenario == "query":
        qs = []
        for t in ("scifact", "germanquad"):
            _, q, _ = load_task(t); qs += [fmt_query(a.style, t, x) for x in q.values()]
        RNG.shuffle(qs); it = __import__("itertools").cycle(qs)
        lats = []; toks = 0
        async with httpx.AsyncClient(timeout=600) as ac:
            for i in range(a.nq):
                v, u, lat = await CL.embed(ac, URLS[0], [next(it)], "query"); lats.append(lat); toks += u
        print(f"### Single query, one at a time ({a.nq} queries, mean {toks / a.nq:.0f} tokens incl. instruction)\n")
        print("| p50 | p95 | p99 | mean |\n|---:|---:|---:|---:|")
        print(f"| {st.median(lats)*1000:.1f} ms | {pct(lats,95)*1000:.1f} ms | {pct(lats,99)*1000:.1f} ms | {st.mean(lats)*1000:.1f} ms |\n", flush=True)
        print("### Queries under load (one query per request)\n")
        print("| Clients | Queries/s | p50 | p95 |\n|---:|---:|---:|---:|")
        for C in map(int, a.levels.split(",")):
            r = await level(C, lambda: [next(it)], a.duration)
            print(f"| {C} | {r['ips']:,.0f} | {r['p50']*1000:.1f} ms | {r['p95']*1000:.1f} ms |", flush=True)
    elif a.scenario == "long":
        print("### One long document per request\n")
        print("| Target tokens | Tokens | Latency (median of reps) | Input tok/s |\n|---:|---:|---:|---:|")
        async with httpx.AsyncClient(timeout=3600) as ac:
            for T in map(int, a.long.split(",")):
                rs = []
                for _ in range(a.reps):
                    v, u, lat = await CL.embed(ac, URLS[0], [chunk(T)]); rs.append((lat, u))
                lat = st.median(x[0] for x in rs); u = st.median(x[1] for x in rs)
                print(f"| {T:,} | {u:,.0f} | {lat:.3f} s | {u/lat:,.0f} |", flush=True)

asyncio.run(main())
