# vLLM 0.33.0, Docker — Hy3 FP8 on four cards

| | |
|---|---|
| Engine | `vllm/vllm-openai:v0.33.0` |
| Checkpoint | [`tencent/Hy3-FP8`](https://huggingface.co/tencent/Hy3-FP8) — 301 GB, FP8 with static scales |
| Cards | 4 of 4, TP=4 |
| KV pool | 307,936 tokens, FP8 — 1.17 full-length requests |
| VRAM per card | 88,497 MiB |
| Start to ready | **301 s** — weights 30 s, engine init 207 s including 48 s of compilation |

```
vllm serve tencent/Hy3-FP8 --served-model-name cyberlink
  --host 127.0.0.1 --port 8000
  --tensor-parallel-size 4 --gpu-memory-utilization 0.90 --max-model-len 262144 --trust-remote-code
  --kv-cache-dtype fp8
  --default-chat-template-kwargs '{"reasoning_effort":"high"}'
  --reasoning-parser hy_v3 --tool-call-parser hy_v3 --enable-auto-tool-choice
```

Both parsers ship with vLLM 0.33. The model card recommends serving with its MTP head; this
run leaves it off, like the other vLLM runs on these cards.

## Pinned values

The chat template reads `reasoning_effort` with three values: `no_think`, its own default,
`low` and `high`. This server makes `high` the default, so a client that sends nothing gets
the thinking model; `no_think` goes in `chat_template_kwargs`.

| Request, short arithmetic question | completion tokens | reasoning text |
|---|---|---|
| nothing (server default `high`) | 94 | 215 characters |
| `chat_template_kwargs: {reasoning_effort: "no_think"}` | 7 | none |

`usage.completion_tokens_details.reasoning_tokens` stays 0 in both: vLLM 0.33 does not count
reasoning tokens for the `hy_v3` parser, although it moves the text into its own field. The
check the protocol prescribes cannot see this switch; completion tokens and the reasoning field
can.
