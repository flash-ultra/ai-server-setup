# vLLM B12X — NVFP4 on two cards

The [`dsv4-flash-nvfp4-sm120` kit](https://github.com/hikarioyama/dsv4-flash-nvfp4-sm120)
run on [cloudscale `GPU2-512-80-4-800`](../../README.md), verified against the numbers it
publishes. Tested 2026-08-17.

| | |
|---|---|
| Engine | vLLM `v0.11.2.dev279+chthonic.consecration.f1190eab.b12x0ff2847.thinkfix.pr20.cu132` |
| Image | `voipmonitor/vllm:chthonic-consecration-f1190eab-b12x0ff2847-pr20-cu132` |
| Checkpoint | [`nvidia/DeepSeek-V4-Flash-NVFP4`](https://huggingface.co/nvidia/DeepSeek-V4-Flash-NVFP4) — 157 GB, 59 files |
| Cards | 2 of 4 (TP=2), cards 0 and 1 |
| Context served | 262,144 |
| Speculation | MTP, 2 draft tokens, B12X MoE backend |
| KV cache | fp8, block size 256 |

## Configuration in effect

```bash
MODEL_DIR=/mnt/scratch/models/DeepSeek-V4-Flash-NVFP4 PORT=8000 SPEC=1 \
  UTIL=0.93 MAXLEN=262144 MNBT=2048 ./serve_b12x_tp2.sh
```

which resolves to:

```
--tensor-parallel-size 2 --moe-backend b12x --linear-backend b12x
--attention-backend B12X_MLA_SPARSE
--kv-cache-dtype fp8 --block-size 256 --load-format safetensors
--gpu-memory-utilization 0.93 --max-model-len 262144 --max-num-seqs 64
--max-num-batched-tokens 2048 --max-cudagraph-capture-size 192
--async-scheduling --no-scheduler-reserve-full-isl
--enable-chunked-prefill --enable-prefix-caching --enable-flashinfer-autotune
--compilation-config {"cudagraph_mode":"FULL_AND_PIECEWISE","custom_ops":["all"]}
--tokenizer-mode deepseek_v4 --reasoning-parser deepseek_v4
--tool-call-parser deepseek_v4 --enable-auto-tool-choice
--speculative-config {"method":"mtp","num_speculative_tokens":2,
                      "draft_sample_method":"probabilistic",
                      "moe_backend":"b12x","use_local_argmax_reduction":true}
--served-model-name DeepSeek-V4-Flash --host 127.0.0.1
```

## Scenarios

| Scenario | Status |
|---|---|
| [Single stream](scenarios/single-stream.md) | measured — 159–163 tok/s decode, TTFT 173–193 ms, 64.6 % acceptance |
| [Concurrent load](scenarios/concurrent-load.md) | measured — ladder run twice, peak 9.97 req/s at C=256 |
| [Reasoning cost](scenarios/reasoning-cost.md) | measured — and the reasoning share is unreportable here |
| Long context | not measured. 262,144 was served and the pool sized for 4.08 concurrent requests at that length, but no long prompt was ever sent |

## Startup

Both figures are wall clock from `docker run` to `Application startup complete`, TP=2,
weights on the local scratch disk.

| Start | Compile cache | Time |
|---|---|---|
| first | empty | **18 min 26 s** |
| second | warm | **18 min 2 s** |

**A warm compile cache saves 24 seconds of 18 minutes.** The breakdown from the first
start explains why: engine init took 974.91 s, of which `torch.compile` was **18.16 s**
and **CUDA-graph capture 676 s**. Capture happens on every start and is not cacheable, so
there is no fast restart to reach for — plan every configuration change as a fresh
19-minute wait. The image pull sits on top of that the first time.

The kit's `serve_b12x_tp2.sh` mounts no cache directory at all, so the 18 s were being
paid again on every start. Adding a mount is worth doing for correctness of the config,
but not for the clock.

## The KV pool is set by the batch budget, not by VRAM

`--max-num-batched-tokens` is documented in vLLM as a scheduling knob. On this checkpoint
it is also the single biggest lever on KV capacity, because DeepSeek-V4's fp32
`CompressorStateCache` is reserved in proportion to it.

| `--max-num-batched-tokens` | Available KV memory | Pool | Per token | Concurrency at 262,144 |
|---|---|---|---|---|
| 512 | 7.83 GiB | 1,664,912 tokens | 4.93 KB | 6.35× |
| 2048 | 7.52 GiB | 1,069,503 tokens | 7.37 KB | 4.08× |

**The memory is the same; the per-token cost is not.** Available KV memory differs by 4 %
between the two runs, while the pool differs by 56 % — so the smaller batch budget does not
free VRAM, it makes each token slot 33 % cheaper. Any reasoning of the form "the pool is
small because the weights are large" is wrong here.

The kit publishes 1,925,540 tokens at `MAXLEN=1048576 MNBT=512` and the reference run for
this machine's configuration reports 1,870,000 at `MAXLEN=262144 MNBT=512`. This machine
measures 1,664,912 for that configuration — **11 % short of the reference, unexplained.**
Same flags, same `UTIL`, different image build is the only candidate that was not ruled
out.

The trade is not free in the other direction either, which is what makes this a pinned
value rather than a recommendation:

## Pinned values

**`--max-num-batched-tokens` must be 2048, not 512.** At 512 the B12X compressed-MLA
kernel locks a 204.82 MB workspace and then needs 215.49 MB once 16 requests run
concurrently:

```
RuntimeError: Worker failed with error 'Workspace is locked but allocation from
'b12x.py:274:_run_compressed_mla' requires 215.49 MB, current size is 204.82 MB.
```

The engine dies and every subsequent request returns HTTP 500. **The container exits with
status 0**, so nothing short of reading the log distinguishes this from a clean shutdown —
and with `--restart unless-stopped` it would come back up and die again on the next burst.
Single-stream and concurrency 8 are unaffected, which is how this configuration passes a
smoke test. [Full measurement](scenarios/concurrent-load.md#--max-num-batched-tokens-512-fails-at-concurrency-16).

**`SPEC=1` requires the B12X path, not MARLIN.** The kit's `serve-mtp.sh` runs MTP on the
MARLIN path, where the draft head dequantises to noise and acceptance falls to ~0 %. Not
measured here — taken from the kit, which documents the fix as landed on B12X only. The
consequence to watch for is silent: output stays valid, speculation just stops paying.

**`--served-model-name` is `DeepSeek-V4-Flash`, capitalised.** The kit's own `ready.sh`,
`smoke.sh` and `mtp_accept.sh` all request `deepseek-v4-flash` in lower case, which this
server does not serve. `ready.sh` therefore never matches and runs to its timeout on a
server that is up; the two others fail their requests silently because output is discarded.
`ready.sh` additionally defaults `NAME=dsv4` while the container is `dsv4b12x`.

## Deviations from the kit as shipped

Two edits, both with `.orig` backups on the machine.

**`--host 0.0.0.0` → `--host 127.0.0.1`.** The kit starts the container with
`--network host`, so binding to all interfaces publishes an unauthenticated inference
endpoint on the machine's public IP; with host networking there is no port mapping left to
restrain it. The kit's own README states the intent — "vLLM binds to 127.0.0.1 only,
outside access goes through LiteLLM" — but `b12x_inner.sh` does not implement it.

The consequence is worth stating because it is easy to trip over: a gateway container on a
bridge network can no longer reach the server, since loopback is only loopback from the
host's own namespace. Either run the gateway with `--network host` too, or bind to the
machine's private address instead.

**Added `-v /mnt/scratch/torch-cache:/root/.cache`.** See [startup](#startup) — worth 24
seconds, kept because a configuration that discards its own compile cache is misleading to
read.

## Operation

```bash
# state
docker ps --filter name=dsv4b12x --format '{{.Names}} {{.Status}}'
curl -s http://127.0.0.1:8000/v1/models | python3 -m json.tool

# KV pool as sized at startup
docker logs dsv4b12x 2>&1 | grep -E "GPU KV cache size|Maximum concurrency for"

# MTP acceptance, cumulative since start
curl -s http://127.0.0.1:8000/metrics | grep -E "spec_decode_num_(accepted|draft)_tokens_total"
```

Acceptance from those two counters is `accepted/drafted`; mean acceptance length is
`1 + accepted/(drafted/2)` — the divisor is the step count, and this configuration drafts
two tokens per step. The kit's script divides by the draft count instead and under-reports.

There is no `--restart unless-stopped` in the kit's script. On this machine that was left
alone: an engine that dies from the workspace lock would be restarted into the same
configuration and die again, so an automatic restart would convert a visible failure into
a loop.

## Still open

- [`--max-num-seqs` above 64](scenarios/concurrent-load.md#not-measured) — the leading
  explanation for both the throughput dip at concurrency 64 and cards that never pass 87 %.
  The one experiment that would turn a reading into a finding
- [A batch budget between 512 and 2048](scenarios/concurrent-load.md#not-measured) —
  whether the 56 % larger KV pool is reachable without crossing the workspace lock
- [Long context](#scenarios) — the pool was sized for 262,144 and nothing longer than
  ~1200 tokens was ever sent. The kit's 1M claim is capacity-verified only, and the
  configuration it needs is the one that fails under load
- [Why the pool is 11 % below the reference](#the-kv-pool-is-set-by-the-batch-budget-not-by-vram)
- [Whether `reasoning_content` is populated](scenarios/reasoning-cost.md#not-measured)
  even though `reasoning_tokens` is not

### Not planned

- **MTP off as a control on this machine.** The kit publishes +38 % from speculation and
  this machine reproduces the "on" half of that comparison closely, so the remaining value
  is confirmation rather than decision-making — at the price of a 19-minute restart plus a
  second one to get back. Dropped deliberately, not overlooked
- **MARLIN path.** Slower by the kit's own numbers (~64 tok/s single-stream against 159)
  and its MTP is broken. Nothing to decide
