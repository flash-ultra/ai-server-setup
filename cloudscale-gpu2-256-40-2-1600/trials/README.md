# Trials

Engines and techniques that were **evaluated and not adopted** on
[cloudscale `GPU2-256-40-2-1600`](../README.md).

**Nothing here is protocol `v1`.** Each file carries its own method, and the numbers are
not comparable with the model directories next door. They exist because the reasoning —
what was tried, what it cost, why it was dropped — is worth more than the throughput
figure, and because without it the same idea comes back in three months as a new one.

Rules for this level:

- **A trial states its own method** and says plainly that it is not `v1`.
- **Numbers from here never move up.** They do not enter the machine README's model table
  or the repository's model matrix. Cross-reference, do not copy.
- **A trial that gets adopted stops being a trial.** It then becomes a `<model>/<setup>/`
  directory with a proper `v1` series, and the trial file is replaced by a link.

| Trial | Verdict |
|---|---|
| [FreeToken](freetoken.md) | Not for production serving. Viable as a second model on the otherwise idle card, with a hard context limit. |

## Related, but not a trial

**llama.cpp's ceiling on this hardware** lives in the
[machine README](../README.md#llamacpp-cannot-split-across-these-cards) rather than here.
It is not an evaluated-and-dropped engine — it is the only engine that loads two of the
measured models, and the finding constrains every future model choice. It belongs to the
hardware, not to a trial.
