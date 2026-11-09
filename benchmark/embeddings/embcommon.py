"""Shared parts of embbench.py and embeval.py: datasets from the local HF cache, HTTP client.
Fetch the datasets first: hf download --repo-type dataset mteb/scifact (and mteb/germanquad-retrieval,
mteb/germanquad-retrieval-qrels, mteb/GermanDPR, mteb/GerDaLIRSmall)."""
import json, os, glob, random, time
import pyarrow as pa
from huggingface_hub import snapshot_download

def _snap(repo):
    return snapshot_download(repo, repo_type="dataset", local_files_only=True)

def _arrow(path):
    with pa.memory_map(path) as src:
        try:
            return pa.ipc.open_stream(src).read_all().to_pylist()
        except Exception:
            src.seek(0); return pa.ipc.open_file(src).read_all().to_pylist()

def load_task(task):
    """corpus {id: text}, queries {id: text}, qrels {qid: {did: rel}} (test split)"""
    if task == "scifact":
        d = _snap("mteb/scifact")
        corpus = {}
        for l in open(f"{d}/corpus.jsonl"):
            r = json.loads(l); corpus[str(r["_id"])] = (r.get("title", "") + " " + r["text"]).strip()
        queries = {str(json.loads(l)["_id"]): json.loads(l)["text"] for l in open(f"{d}/queries.jsonl")}
        qrels = {}
        for i, l in enumerate(open(f"{d}/qrels/test.tsv")):
            if i == 0: continue
            q, did, s = l.rstrip("\n").split("\t"); qrels.setdefault(q, {})[did] = int(s)
    elif task == "germanquad":
        d = _snap("mteb/germanquad-retrieval"); dq = _snap("mteb/germanquad-retrieval-qrels")
        corpus = {str(r["_id"]): ((r.get("title") or "") + " " + r["text"]).strip()
                  for f in sorted(glob.glob(f"{d}/corpus/*.arrow")) for r in _arrow(f)}
        queries = {str(r["_id"]): r["text"] for f in sorted(glob.glob(f"{d}/queries/*.arrow")) for r in _arrow(f)}
        qrels = {}
        for f in sorted(glob.glob(f"{dq}/test/*.arrow")):
            for r in _arrow(f):
                qrels.setdefault(str(r["query-id"]), {})[str(r["corpus-id"])] = int(r["score"])
    elif task == "germandpr":
        import pyarrow.parquet as pq
        d = _snap("mteb/GermanDPR"); rd = lambda n: pq.read_table(glob.glob(f"{d}/{n}/*.parquet")[0]).to_pylist()
        corpus = {str(r["id"]): ((r.get("title") or "") + " " + r["text"]).strip() for r in rd("corpus")}
        queries = {str(r["id"]): r["text"] for r in rd("queries")}
        qrels = {}
        for r in rd("qrels"): qrels.setdefault(str(r["query-id"]), {})[str(r["corpus-id"])] = int(r["score"])
    elif task == "gerdalir":
        d = _snap("mteb/GerDaLIRSmall")
        corpus = {}
        for l in open(f"{d}/corpus.jsonl"):
            r = json.loads(l); corpus[str(r["_id"])] = ((r.get("title") or "") + " " + r["text"]).strip()
        queries = {str(json.loads(l)["_id"]): json.loads(l)["text"] for l in open(f"{d}/queries.jsonl")}
        qrels = {}
        for l in open(f"{d}/qrels/test.jsonl"):
            r = json.loads(l); qrels.setdefault(str(r["query-id"]), {})[str(r["corpus-id"])] = int(r["score"])
    else:
        raise SystemExit(f"unknown task {task}")
    queries = {q: t for q, t in queries.items() if q in qrels}
    return corpus, queries, qrels

def text_pool():
    """Mixed English and German text for synthetic chunks."""
    parts = []
    for t in ("scifact", "germanquad"):
        c, _, _ = load_task(t); parts += list(c.values())
    random.Random(7).shuffle(parts)
    return "\n\n".join(parts)

# Prompt format per model family (documents without instruction, except nemotron/gemma2)
INSTR = {"scifact": "Given a scientific claim, retrieve documents that support or refute the claim",
         # German tasks: MTEB has no task prompt there and falls back to the retrieval default
         "germanquad": "Retrieve text based on user query.",
         "germandpr": "Retrieve text based on user query.",
         "gerdalir": "Retrieve text based on user query."}
INSTR_OWN = {"germanquad": "Given a question, retrieve passages that answer the question",
             "germandpr": "Given a question, retrieve passages that answer the question",
             "gerdalir": "Given a passage from a German court decision, retrieve the court decisions it refers to"}
if __import__("os").environ.get("EMB_INSTR") == "own": INSTR.update(INSTR_OWN)
def fmt_query(style, task, q):
    i = INSTR[task]
    if style == "qwen": return f"Instruct: {i}\nQuery:{q}"
    if style == "harrier": return f"Instruct: {i}\nQuery: {q}"
    if style == "gemma2": return f"task: search result | query: {q}"
    return q  # bge, nemotron (prefix via input_type)
def fmt_doc(style, d):
    if style == "gemma2": return f"title: none | text: {d}"
    return d

class Client:
    """embed() over an httpx.AsyncClient; OpenAI /v1/embeddings or the Cohere-style /v2/embed."""
    def __init__(self, urls, model, api="openai", truncate=None):
        self.urls = urls; self.model = model; self.api = api; self.truncate = truncate
    async def embed(self, ac, url, texts, input_type="document"):
        t0 = time.perf_counter()
        if self.api == "v2":
            body = {"model": self.model, "input_type": input_type, "embedding_types": ["float"], "truncate": "END",
                    "inputs": [{"content": [{"type": "text", "text": t}]} for t in texts]}
            r = await ac.post(f"{url}/v2/embed", json=body)
            r.raise_for_status(); j = r.json()
            vecs = j["embeddings"]["float"]
            m = j.get("meta") or {}; u = (m.get("billed_units") or {}).get("input_tokens") or (j.get("usage") or {}).get("prompt_tokens") or 0
        else:
            body = {"model": self.model, "input": texts, "encoding_format": "float"}
            if self.truncate: body["truncate_prompt_tokens"] = self.truncate
            r = await ac.post(f"{url}/v1/embeddings", json=body)
            r.raise_for_status(); j = r.json()
            vecs = [d["embedding"] for d in sorted(j["data"], key=lambda d: d["index"])]
            u = (j.get("usage") or {}).get("prompt_tokens") or 0
        return vecs, u, time.perf_counter() - t0
