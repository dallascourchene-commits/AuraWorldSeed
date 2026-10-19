# October 2026 additional Aura research benchmarks

**Status:** source-attested historical software results; independently runnable *subset* published below. The research archives are not official competition evaluations or experimental chemistry. This directory supplements, and does not replace, the earlier [public benchmark ledger](../README.md).

| Source / workload | Reported result | Proper interpretation |
|---|---:|---|
| **10D D11 four-engine ARC** vs D38 native (same archived ARC-AGI-2 public training task IDs; nominal 160-probe allocations) | **33/500 vs 31/500**, but **348.2 s vs 0.95 s** | 2 net additional exact training-task solves at very large orchestration cost. Probe counters differ across engines, so this is NOT equal compute. Not official ARC evaluation. |
| **10D D10 single DSL ARC** | **21/500** on archived public-training tasks, of which **11/200** were frozen before scoring its last 200 source IDs | First 300 were development/feedback tasks. Source JS is preserved here for user-run exploration. Not blind/uncontaminated generalization. |
| **Tessera D9 SDC exact domain surrogate** | **256/256** four-bit addition input pairs, **88/88** randomized exact checks | Algebraic finite-state addition model, not the original DNA sequences, reaction kinetics or molecular yield. |
| **Tessera D9 incremental transfer-matrix updates** | **~2,204×** median at 32,768 positions after tree build (120 updates × three reps) | Python local single-site update vs repeated full recalculation. Precomputation and O(N) memory are excluded from that speed figure. |
| **Original Aura VMC-002** | **35.840×** same-structured-case quotient/local route, **0.9847×** high entropy | An algorithmic structured-regime result, not universal improvement. [Full public verifier](../VIRTUAL_MEMORY_CRYSTAL.md). |
| **A few hundred byte launcher files** | e.g. `cartridges/game.html` is **765 bytes** while its encoded payload is **80,440 bytes** | Distinguish a launcher wrapper from all assets/code needed to run a game. |
| **Claim: ~600-byte generative seed → ~135 MB video** | **HOLD_EXACT_PUBLIC_REPRODUCTION** | A portable source-seed recipe, deterministic playback, byte counts, media comparison, and runnable independent receipt are required before listing a ratio as validated. |

The 10D ARC training dataset and frozen score receipts were supplied as source archives dated October 15, 2026. This release does not publish private Drive document IDs or rehost the research data. The ARC DSL is the exact original 10D standalone solver, not the later more expensive D11 coordinator.

## Reproduce from source

**Minimal no-download mathematical canary:** `python3 benchmarks/october-2026/sdc_paper_level.py` and `python3 benchmarks/october-2026/validate_exhaustive_n4.py`. The exact-algorithm tests do not require chemistry equipment. For a faster CI run, only run `validate_exhaustive_n4.py`; `sdc_paper_level.py` runs extended timing tests and will replace local output JSON files. Report the CPU model, Python version, initialization overhead, trial count and resident-memory method when comparing timing.

**ARC candidate search:** `node benchmarks/october-2026/aura_arc_solver_d10.js` loads the module only. To run a public training task, import `const {search}=require('./aura_arc_solver_d10.js')`, prepare `{train:[{input:[[...]],output:[[...]]}],test:[{input:[[...]]}]}`, call `search(task)`, and score the returned `predictions` against hidden gold **only after writing a frozen candidate commitment**. For the original 500-task scored result, reproduce from an authorized copy of the public ARC-AGI-2 training split; this release does not falsely claim its 500-task replay has been independently rerun on GitHub.

**CI**: [October software checks](../../.github/workflows/reproduce-october-2026.yml) and the existing [Core](../../.github/workflows/reproduce-benchmarks.yml) and [VMC](../../.github/workflows/reproduce-vmc.yml) workflows.

**Scar preservation:** D11's tiny accuracy gain caused a large slowdown. D9's off-target energy bias can make the wrong ground state preferred. Structured compression has high-entropy controls. Public records should preserve negative results, not replace them with broad claims.
