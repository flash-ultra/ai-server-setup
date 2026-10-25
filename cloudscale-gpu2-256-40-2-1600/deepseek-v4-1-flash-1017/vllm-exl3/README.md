# vLLM + EXL3 plugin — the pack's own recipe

Not a stock image and not a community patchset: the checkpoint ships the container that
serves it. `recipe/build.sh` compiles five sm120 kernels and `recipe/serve/serve.sh`
starts vLLM with the `vllm_exl3` plugin and the configuration behind the author's
published numbers.

## What it took to get running

| Step | Time | Outcome |
|---|---|---|
| `hf download` of the pack | 5 min | 315 GiB on `/mnt/scratch` |
| `recipe/build.sh` | 9 min | image `dsv41-flash-1017-exl3-3bpw-sm120`, 35.4 GB, RC=0 |
| First engine start | 9 min | weights, Engram tables and kernel caches |

**The build needs no GPU.** All five kernels compile from `TORCH_CUDA_ARCH_LIST=12.0a`
against the CUDA toolkit in the base image, so the card stays free for whatever is still
serving. Worth knowing before scheduling a swap-over window.

**The pack's stated host requirement is a container cap, not a hardware floor.** The
README asks for 260 GiB of host RAM; that figure is `CONTAINER_MEM`, and `serve.sh`
line 10 states the actual demand as *"The container uses ~230 GiB of host RAM"*. On a
251 GiB machine the difference decides whether it runs at all. Measured in operation:
**230 GiB with the chat model alone, 237 GiB with the embedding model beside it.**

## Two configurations, and which numbers belong to which

Everything in `scenarios/` was measured on the **measurement** column. The machine
serves the **production** column, which trades window for a co-tenant.

| | measurement | production |
|---|---|---|
| `MAX_MODEL_LEN` | 1,048,576 | **327,680** |
| `KV_MEM` | 4.25 GiB | 2 GiB |
| KV pool | 1,071,558 tokens | — |
| `MAX_NUM_SEQS` | 8 | **32** |
| `UTIL` | 0.92 | **0.905** |
| `SERVED` | `deepseek-v4.1-flash` on 8010 | `cyberlink` on 8001 |
| VRAM per card | 87,627 MiB | 89,704 MiB |
| Second model on the cards | none | [Qwen3-Embedding-4B](../../qwen3-embedding-4b/), 6,520 MiB |

Everything else is the script's default: `TP=2`, `--max-num-batched-tokens 16384`,
`--kv-cache-dtype fp8`, `--block-size 64`, `--quantization exl3`, DSpark speculation at
`k=5`, `VISION=1`.

**Lowering `UTIL` does not shorten the window.** The served length is pinned by the
explicit `--kv-cache-memory`, so 0.905 and 0.92 both give 327,680 tokens and a
330,402-token pool; the fraction only decides how much the engine may hold in total.
That is what made it the right thing to give up when the embedding needed room.

```
serve --tensor-parallel-size 2 --host 0.0.0.0 --port $PORT --api-key $API_KEY
  --max-model-len 327680 --kv-cache-dtype fp8 --kv-cache-memory 2147483648
  --gpu-memory-utilization 0.92 --max-num-seqs 32 --max-num-batched-tokens 16384
  --kernel-config '{"enable_flashinfer_autotune":false,"enable_jit_warmup":false}'
  --block-size 64 --quantization exl3
  --tokenizer-mode deepseek_v41 --tool-call-parser deepseek_v41 --enable-auto-tool-choice
  --reasoning-parser deepseek_v41
  --served-model-name cyberlink --trust-remote-code
```

## Pinned values

| Setting | Value | What happens if you deviate |
|---|---|---|
| `MAX_MODEL_LEN` ≤ 333,056 at `KV_MEM=2 GiB` | **327,680** | the engine refuses to start: `To serve at least one request with the model's max seq len (524288), 2.58 GiB KV cache is needed, which is larger than the available KV cache memory (2.0 GiB)` — and names the ceiling itself, `estimated maximum model length is 333056`. The two numbers move together; shrinking the window is what buys the co-tenant its memory |
| `API_KEY` | required | `serve.sh` aborts on an unset key before touching the GPU. Clients send it as a bearer token; the [router](#routing-and-restart) injects it so the gateway does not have to |
| `CPU_EXPERTS` | **0**, forced | `check_host.sh` fails on this guest — no AVX-512, not even AVX2. Setting `CPU_EXPERTS_STRICT=1` turns the fallback into an abort |
| `--max-num-seqs` | 8 by default | the pack is tuned for a few long sessions. Requests past the slot count queue rather than batch, and a concurrency ladder above it [measures the queue](scenarios/concurrent-load.md) |
| `NCCL_P2P_DISABLE` | 0 | the 8-bit all-reduce needs PCIe P2P, verified working in both directions on these cards |

**The window is the lever on this machine, not the utilisation.** The weights take the
same room whatever the fraction says; what the window changes is the KV reservation,
and that is the only thing a second model can be carved out of.

## Routing and restart

Chat and embeddings sit behind one port because the gateway expects a single upstream.
`api-router.py` dispatches on the request path — anything containing `/embeddings` goes
to 8002, everything else to 8001 — and injects the chat upstream's bearer token, which it
reads from `~/.chat-api-key` so the key stays out of the gateway configuration.

**`serve.sh` runs in the foreground and starts its container with a hardcoded `--rm`**,
which rules out a Docker restart policy: `--restart` and `--rm` conflict. Started by
hand under `nohup` the model therefore does **not** come back after a reboot. Two
systemd units fix it:

| Unit | Role |
|---|---|
| `cyberlink-embed.service` | starts the embedding container, `Restart=always` |
| `cyberlink-chat.service` | runs `serve.sh` with the production environment, `Restart=always`, `RequiresMountsFor=/mnt/scratch`; its wrapper polls `:8002` first, bounded at five minutes so a broken embedding cannot keep the chat model down |

**The embedding goes first, and that order is load-bearing.** Both services size
themselves as a fraction of the whole card and vLLM's startup check compares the
*requested* fraction against free memory, so whichever starts second has to find its
share still free. The chat model's check is the tighter one — it wants 87.37 GiB at
0.92 — and it is also the one that grows after startup: measured, it holds 87,627 MiB
when it reports ready and 91,076 MiB once warmup has run, which is 3,449 MiB the
embedding can no longer have. Starting the small service first and the growing one
second is what makes both checks pass.

Getting the two fractions right took four attempts and is written up on the
[embedding's setup page](../../qwen3-embedding-4b/vllm/README.md#start-order-is-part-of-the-configuration),
including the measurement that misled the first three: the same embedding occupies
9,213 MiB when it starts first and 6,265 MiB when it starts second. **A footprint
measured as the second service is a leftover, not a requirement.**
