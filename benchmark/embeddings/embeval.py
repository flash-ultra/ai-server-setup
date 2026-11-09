#!/usr/bin/env python3
"""Retrieval quality through the server: nDCG@10 and Recall@10/100, exact search (cosine).
  embeval.py --urls ... --style qwen|harrier|bge|nemotron|gemma2 [--api v2] --task scifact|germanquad|germandpr|gerdalir"""
import argparse, asyncio, math, sys, time
import httpx, numpy as np
sys.path.insert(0, __import__("os").path.dirname(__file__))
from embcommon import Client, load_task, fmt_query, fmt_doc

ap = argparse.ArgumentParser()
ap.add_argument("--urls", required=True); ap.add_argument("--model", default="cyberlink")
ap.add_argument("--api", default="openai"); ap.add_argument("--style", required=True)
ap.add_argument("--task", required=True); ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--conn", type=int, default=16); ap.add_argument("--truncate", type=int, default=8192)
a = ap.parse_args()
URLS = a.urls.split(","); CL = Client(URLS, a.model, a.api, a.truncate)

async def embed_all(texts, itype):
    out = [None] * len(texts); toks = [0]; idx = list(range(0, len(texts), a.batch)); pos = [0]
    async def worker(i):
        async with httpx.AsyncClient(timeout=3600) as ac:
            while pos[0] < len(idx):
                s = idx[pos[0]]; pos[0] += 1
                v, u, _ = await CL.embed(ac, URLS[i % len(URLS)], texts[s:s + a.batch], itype)
                out[s:s + len(v)] = v; toks[0] += u
    t0 = time.perf_counter(); await asyncio.gather(*[worker(i) for i in range(a.conn)])
    m = np.asarray(out, dtype=np.float32); m /= np.linalg.norm(m, axis=1, keepdims=True)
    return m, toks[0], time.perf_counter() - t0

def ndcg10(ranked, rel):
    dcg = sum((2 ** rel.get(d, 0) - 1) / math.log2(i + 2) for i, d in enumerate(ranked[:10]))
    ideal = sorted(rel.values(), reverse=True)[:10]
    idcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg else 0.0

async def main():
    corpus, queries, qrels = load_task(a.task)
    dids = list(corpus); qids = list(queries)
    D, dt, dsec = await embed_all([fmt_doc(a.style, corpus[d]) for d in dids], "document")
    Q, qt, qsec = await embed_all([fmt_query(a.style, a.task, queries[q]) for q in qids], "query")
    S = Q @ D.T; top = np.argsort(-S, axis=1)[:, :100]
    n10 = []; r10 = []; r100 = []
    for i, q in enumerate(qids):
        ranked = [dids[j] for j in top[i]]; rel = {d: s for d, s in qrels[q].items() if s > 0}
        n10.append(ndcg10(ranked, rel)); rs = set(rel)
        r10.append(len(rs & set(ranked[:10])) / len(rs)); r100.append(len(rs & set(ranked)) / len(rs))
    print(f"| {a.task} | {len(dids):,} docs / {len(qids):,} queries | dim {D.shape[1]} | nDCG@10 {np.mean(n10):.4f} | R@10 {np.mean(r10):.4f} | R@100 {np.mean(r100):.4f} | corpus {dt:,} tok in {dsec:.1f} s ({dt/dsec:,.0f} tok/s) | queries {qt:,} tok in {qsec:.1f} s |")

asyncio.run(main())
