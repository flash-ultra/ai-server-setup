# vLLM + EXL3, the pack's own recipe — DeepSeek-V4.1-Flash-1017 EXL3 3 bpw on four cards

The [EXL3 pack measured on two cards](../../../cloudscale-gpu2-256-40-2-1600/deepseek-v4-1-flash-1017/vllm-exl3/README.md),
here with the pack's own four-card profile. Built and measured 2026-11-07.

| | |
|---|---|
| Pack | [`diffbot/DeepSeek-V4.1-Flash-EXL3-3bpw-2x-RTX-PRO-6000`](https://huggingface.co/diffbot/DeepSeek-V4.1-Flash-EXL3-3bpw-2x-RTX-PRO-6000) — 322 GiB on disk |
| Engine | the pack's image `dsv41-flash-1017-exl3-3bpw-sm120` (vLLM nightly-5555a2d8 + sm120 patches + `vllm_exl3`, 35.4 GB), built by `recipe/docker/build.sh` in 6 minutes; the four-card kernels by `recipe/kernels/build.sh 8x` in 3 |
| Profile | **`PROFILE=8x REPLICA=0`**: one replica of the pack's eight-card node profile — TP=4 attention, EP=4 routed experts, every expert in VRAM, 1 M context, 128 sequences, DSpark k=7 with the code-tuned drafter head |
| KV pool | **4,538,321 tokens**, FP8 — 4.33 full 1 M-token requests |
| VRAM per card | 87.8–88.1 GB |
| Host RAM | 332 GB in use (Engram int4 tables, embedding, 150 GB CPU KV-offload tier); `CONTAINER_MEM` 400 GB |
| Start to ready | **376 s** — weights 37 s, engine init 256 s, warmup 31 s |
| Thinking | off via `enable_thinking: false` (19 → 0 reasoning tokens) |

## One switch this machine needs: no P2P atomics

The first start hung in the pack's 8-bit prefill all-reduce (`[fp8ar] rank 0 … peer wait
timeout (data) seq 1 … seen 0x0`) and the engine died with `CUBLAS_STATUS_INTERNAL_ERROR`.
The pack's own all-reduce kernels synchronise the cards through atomic flags in each other's
memory, and this VM does not support peer atomics:

```
nvidia-smi topo -p2p r   →  OK between all four cards
nvidia-smi topo -p2p w   →  OK
nvidia-smi topo -p2p a   →  NS  (not supported)
```

The two-card machine has them, which is why the recipe works there unchanged. Every
custom all-reduce was switched to NCCL through the recipe's own environment switches:

```
DS41_FP8AR=0 DS41_AR8_TP4=0 DS41_AR8_HIER=0 DS41_AR8_GRAPH=0 DS41_CAR=0 DS41_CAR_PCIE_IPC=0
```

The numbers on this page are therefore the NCCL path. On a host with peer atomics the
pack's 8-bit all-reduces should make them faster, not slower.

## Two more things the pack needs from a Hugging Face cache

- **Copy the recipe out of the cache.** `hf download` stores the pack as symlinks into a
  shared `blobs` folder; `docker build` does not follow symlinks out of its context. The
  recipe (2.5 MB) was copied with `cp -rL` to a real directory; the weights stay in the
  cache and `MODELS_DIR=/opt/llm/hf/hub` mounts the cache including `blobs`.
- **The copied scripts have no execute bit**, because cached files carry none. Call them
  with `bash`.
