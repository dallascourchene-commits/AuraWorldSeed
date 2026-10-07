# AuraWorldSeed Benchmarks

[![Reproduce Core Aura Benchmarks](https://github.com/dallascourchene-commits/AuraWorldSeed/actions/workflows/reproduce-benchmarks.yml/badge.svg)](https://github.com/dallascourchene-commits/AuraWorldSeed/actions/workflows/reproduce-benchmarks.yml)\n\n**Public reproducibility ledger — benchmark harvest for 2026-10-06 through 2026-10-07**

This page consolidates the benchmark work that was spread across Arena receipts, research notes, C++ programs, browser witnesses, and acceptance packets. It intentionally preserves failures, HOLDs, repairs, and claim ceilings instead of reporting only favorable results.

## Why the numbers matter: WITH vs WITHOUT

Where a matched control exists, this ledger now shows it explicitly.

| Test | WITHOUT / control | WITH / treatment | Observed difference | What it means |
|---|---:|---:|---:|---|
| Triad/quartet scheduling | fixed static: **30/66** unique pairs | balanced rotating: **66/66** | **+54.5 percentage points** of pair coverage; pair-count SD **91.7% lower** | structural scheduling improvement |
| HDC HRR binding | direct **O(D²)** convolution | FFT HRR | historical same-carrier result ≈ **130.4×** | implementation speedup with numerical equivalence guard |
| HDC cached binding | direct **O(D²)** convolution | cached-spectrum HRR | historical same-carrier result ≈ **417.3×** | implementation speedup with same reference |
| Exact reification | full source bytes | exact program + residual | structured fixture **132,352 → 1,110 bytes** (≈**119×** smaller) | compression only where exact structure is earned |
| Reification negative control | deterministic/random-like source | exact program + residual | ratio ≈ **1.00**, so **no false compression win** | falsifies cherry-picked compression |
| Gate24 workcells | serial **4.3 ms** | parallel **1.6 ms** | **2.687×** lower latency ratio on that fixture | browser-worker latency only |
| Archangel neural dispatch | pre condition | post condition | median **3.4909×**; heavy touches **−75%** | paired Arena A/B |
| H01 storage accounting | monolithic **1.2 GB** proxy | selective **5.09 MB** | ≈ **235.54×** less addressed storage | computational sparse-manifestation fixture |
| Lineage storage | full child copy **54,612,970 B** | exact patch **21,570 B** | **2,531.9×** smaller incremental storage | exact source-pair delta |
| Four-parent lift | roots without gate-specific evidence: **1/24** | explicit evidence cartridge: **24/24** | HOLD → PASS | validity/control improvement, not speed |
| Physical-completion judge | procedural judge closed **100/100** but could overclaim | residual-specific physical canaries | **50/50** physical closures with **1 HOLD + 12 repairs** | stricter validity, not speed |
| 24³ carrier overhead | closed-world mean **744.8 ms** | integrated 9D mean **787.1 ms** | integrated carrier ≈ **5.7% slower** | publishes a cost, not just wins |

Some benchmarks do **not** yet have a clean matched performance baseline. In particular, the standalone Orphanim 24⁴ result is presently a correctness/throughput result; the historical interpreted-JavaScript timeout is not an apples-to-apples control for native C++. RGB tubelets and ARIEL journey fuzzing likewise should not be advertised as performance improvements until a matched control is run.

**Effect size is not automatically statistical significance.** For timing results, independent reviewers should use repeated paired runs on the same machine. The reproducer supports **1, 3, 5, 10, or 20 repetitions**, records the environment, and emits fresh raw JSON plus a comparison summary.

Full independent instructions: **[REPRODUCE.md](REPRODUCE.md)**

## Reproduce without downloading the developer ZIP

You do **not** need the 95 MB developer package.

### One-click GitHub runner

Open:

**Actions → Reproduce Core Aura Benchmarks → Run workflow**

https://github.com/dallascourchene-commits/AuraWorldSeed/actions/workflows/reproduce-benchmarks.yml

GitHub checks out this public repository on its own runner, compiles the standalone sources under `benchmarks/src/`, runs them, and prints fresh receipts into the Actions log. Timing numbers will vary by CPU; correctness/invariance checks are the important reproducibility target.

### Browser-only 24³ closure

Open the self-contained browser benchmark directly:

https://dallascourchene-commits.github.io/AuraWorldSeed/benchmarks/24cube.html

No npm install, build step, server, or developer package is required.

### Local C++20 commands

```bash
g++ -O3 -march=native -std=c++20 benchmarks/src/orphanim_24pow4_bench.cpp -o /tmp/orphanim24
/tmp/orphanim24

g++ -O3 -march=native -std=c++20 benchmarks/src/triad_quartet_lattice_bench.cpp -o /tmp/triadquartet
/tmp/triadquartet 1000000 20261006

g++ -O3 -march=native -std=c++20 benchmarks/src/triad_quartet_projection_unification_bench.cpp -o /tmp/projection
/tmp/projection

g++ -O3 -march=native -std=c++20 benchmarks/src/hdc_dual_frontier_bench.cpp -o /tmp/hdc
/tmp/hdc --statistical-orthogonality

g++ -O3 -march=native -std=c++20 benchmarks/src/reification_frontier_microscope.cpp -o /tmp/reification
/tmp/reification README.md
```

The HDC program has both a deliberately strict literal-orthogonality policy and a calibrated statistical policy. The public workflow uses `--statistical-orthogonality`; the literal policy is retained as a falsifier and can return a typed HOLD.

---

## Reproducibility classes

- **A — standalone:** compact source is in this repository and can be compiled/run independently.
- **B — Arena integration:** depends on the public World Seed/browser runtime; reproduced by entering the Arena rather than by a tiny standalone binary.
- **C — fixture-bound:** algorithm is public/reproducible, but the exact published number depends on a declared source pair or synthetic scale fixture.

## Harvested benchmark index

| Benchmark | Result | Class |
|---|---:|:---:|
| Exact 24³ address/lineage closure | 13,824/13,824 work units; 6 HOLD→repair→resume; independent verification PASS | A |
| 24³ × 24 persistent-browser run | 331,776 work units; 24/24 deterministic root match | A/B |
| Triad/quartet lattice search | 1,000,000 candidate schedules; 66/66 pair coverage; optimal 5/6 full-cycle balance candidate | A |
| 3×4 ↔ 4×3 projection lattice | 1,000,000 reversible transpose/reopen trials; 0 mismatches | A |
| Orphanim 24⁴ structural sweep | 331,776 coordinates; 7,962,624 semantic frames; full semantic invariance | A |
| HDC/VSA dual frontier | D=8192, K=1024; calibrated policy 5/5 PASS; deterministic microbenchmarks | A |
| Reification microscope | exact-reopen representation test; structure-dominant and residual-dominant cases separated | A/C |
| RGB tubelet algebraic media | 29,000-instance render stress ≈54 FPS equivalent on measured carrier | B |
| Gate24 Glass Box | 24/24 gates; 12-way parallel 1.6 ms vs serial 4.3 ms on tiny local workcells | B |
| C++ 100-cycle 4→3→4→3 | 100/100 cycles and 400/400 phases, but physical-completion claim correctly held | B |
| North-Star physical convergence | 50/50 reciprocal physical closures in 51 cycles; 1 HOLD + 12 repairs | B |
| Four-parent 51×4 lift | 204 parent cycles; first child HOLD; repaired child 24/24 Gate24 PASS | B |
| Archangel neural before/after | median 3.4909× clean dispatch speedup; 75% heavy-touch reduction | B |
| H01 selective brain reification | 150M procedural synapse addresses; 0.21228% touched in consequence-local fixture | C |
| Virtual photonic lineage memory | 21,570-byte exact child patch; 2,531.9× smaller incremental storage than duplicating the 54.6 MB parent | C |
| ARIEL recursive-journey fuzz | 51 journeys; 417 receipts; 23 unique stations visited | B/C |

---

## 1. Exact 24³ address / lineage closure

The closure interprets the requested geometry literally:

```text
24 epochs × 24 Gate24 stages × 24 objective rounds = 13,824 work units
```

Published acceptance:

- work receipts: **13,824 / 13,824**
- unique addresses: **13,824 / 13,824**
- unique objectives: **13,824 / 13,824**
- stage closures: **576 / 576**
- epoch closures: **24 / 24**
- address round trips: **13,824 / 13,824**
- mirror involutions: **13,824 / 13,824**
- receipt-chain links: **13,824 / 13,824**
- completed/repaired units: **13,824 / 13,824**
- HOLDs detected: **6**
- side missions completed: **6**
- unresolved required HOLDs: **0**
- final root: `b54707b90f015a0b8318ae953ebe26907e8f552e6eaea5e48da68fc597facab4`

The six HOLDs were preserved: missing depth tag, unsafe Number range, u64 overflow, unbound browser-state bridge, injected tamper, and carrier-shape mismatch. Each repair retained a return pointer to the interrupted coordinate.

**Claim ceiling:** this is a computational address/lineage kernel. Logical `24³` cardinality is not a claim of physical spatial dimensions.

**Reproduce:** [`24cube.html`](24cube.html).

## 2. 24³ repeated 24 times in one persistent browser

```text
24 × (24 × 24 × 24) = 331,776 work units
```

### Standalone closed-world carrier

- completed: **24 / 24**
- deterministic root match: **24 / 24**
- mean per 24³ run: **744.8 ms**
- min / max: **672.4 / 838.9 ms**
- wall time: **18.05 s**
- browser disconnects: **0**
- page errors: **0**
- first→last heap delta: **−2,541,802 bytes**

### Integrated 9DGem V0.4 carrier

- completed: **24 / 24**
- deterministic root match: **24 / 24**
- mean per 24³ run: **787.1 ms**
- min / max: **724.7 / 897.4 ms**
- wall time: **20.93 s**
- browser disconnects: **0**
- page errors: **0**

The integrated Arena exposed a retained lifecycle scar while remaining alive: scene objects **689→804**, AEV frames **31→59**, events **251→536**, and heap **+4,549,960 bytes**. Therefore the result narrowed the earlier browser failure away from recursive cardinality and toward the long-horizon visual/AEV resource lifecycle.

**Keeper:** `24Cube recursion != carrier failure`.

## 3. Triad/quartet lattice scheduling

Source: [`src/triad_quartet_lattice_bench.cpp`](src/triad_quartet_lattice_bench.cpp)

Published 1,000,000-candidate run:

- search: **1,000,000** schedules
- measured search time: **13.72 s** in one recorded run
- measured search rate: **72,867 candidates/s**
- fixed static grid: only **30 / 66** pair relationships
- cyclic no-repeat tour: **48 / 66**
- balanced candidate: **66 / 66**
- full pair coverage by phase **8**
- all operational positions unique in the 24-phase cycle
- pair-count histogram: **36 pairs ×5**, **30 pairs ×6**
- pair standard deviation: **0.49793**
- role-balance score: **1.0**
- bounded 100-world-scale test: **100 / 100**, no structural degradation detected

There are 360 pair contacts across the full 24-phase cycle and 66 possible pairs. Since `360/66` is non-integer, exact equality is impossible; the 5/6 distribution is therefore the minimum possible integer spread.

A separate targeted **40,000,000-step** phase-5 search reached **64/66** relationships but did not find a full phase-5 cover. This does **not** prove phase 5 impossible. Phase 6 remains the fastest observed full-cover schedule, not a theorem of global optimality.

**Claim ceiling:** structural scheduling coverage is not semantic reasoning quality.

## 4. Three projections / four components

Source: [`src/triad_quartet_projection_unification_bench.cpp`](src/triad_quartet_projection_unification_bench.cpp)

Published results:

- matrix: **3 × 4 = 12** unique cells
- transpose/reopen trials: **1,000,000**
- state mismatches: **0**
- root mismatches: **0**
- recorded transpose test: **0.047761 s**
- single-cell locality cases: **12 / 12 PASS**
- procedural stress: **29,000 instances × 120 frames × 12 components**
- component evaluations: **41,760,000**
- recorded time: **0.887618 s**
- recorded rate: **47.047 million component evaluations/s**
- exact `t0` replay: **PASS**
- `t0 != t1`: **PASS**

A scalar-aggregation collision is deliberately retained as a counterexample: unity is reconstructable composition, not averaging.

## 5. Orphanim 24⁴ native structural sweep

Source: [`src/orphanim_24pow4_bench.cpp`](src/orphanim_24pow4_bench.cpp)

Published native C++20 run:

- logical coordinates: **331,776 = 24⁴**
- role permutations: **24**
- semantic frames: **7,962,624**
- role-seat evaluations: **31,850,496**
- base-24 rank round trips: **331,776 / 331,776**
- mirror involutions: **331,776 / 331,776**
- semantic invariance: **7,962,624 / 7,962,624**
- distinct trace sets: **331,776 / 331,776**
- elapsed: **665.997 ms**
- throughput: **11.956 million semantic frames/s**
- status: `PASS_24POW4_ORPHANIM`

The interpreted exhaustive JavaScript route exceeded a 240 s acceptance window on that carrier; the larger deterministic native sweep completed in under one second.

**Claim ceiling:** this measures deterministic addressing/permutation/rebase work. **331,776 logical coordinates are not 331,776 concurrent agents.**

## 6. HDC / VSA dual frontier

Source: [`src/hdc_dual_frontier_bench.cpp`](src/hdc_dual_frontier_bench.cpp)

Fixture:

- dimension: **D = 8192**
- codebook: **K = 1024**
- calibrated statistical policy: **5 / 5 PASS**
- recorded median wall time: **2.680 s**

Recorded same-carrier microbenchmarks included:

- HRR full binding: about **130.4×** faster than the declared direct O(D²) circular-convolution reference
- cached-spectrum HRR: about **417.3×** faster than that same reference
- HRR full binds: about **2,260.5/s**
- cached HRR binds: about **7,234.8/s**
- BSC binds: about **37.1 million/s**
- BSC unbinds: about **44.9 million/s**
- packed permutations: about **9.55 million/s**

These are implementation/carrier microbenchmarks, not universal speedups.

## 7. Exact-reopen reification microscope

Source: [`src/reification_frontier_microscope.cpp`](src/reification_frontier_microscope.cpp)

The microscope partitions source bytes into exact programmatic structure plus residual bytes and refuses lossy substitution.

Representative recorded fixtures:

- structured synthetic fixture: **132,352 → 1,110 bytes**, exact ratio **0.008386**
- random fixture: **131,072 → 131,278 bytes**, ratio **1.001572**, correctly falling back to source-dominant storage
- V5 HTML: **54,612,970 → 54,622,282 bytes**, ratio ≈ **1.00017**, correctly classified residual-dominant rather than pretending the bytes were compressible

This is the intended boundary: **reify structure where earned; preserve exact residual/source where not earned.**

## 8. RGB tubelet algebraic media

Arena/WebGL acceptance:

- procedural lattice: **3,200** instances, **1 draw call**
- program descriptor: **678 bytes**
- discrete Stokes relative error: **3.92e−7**
- logical benchmark: **29,000 instances × 120 frames**
- logical channel evaluations: **10,440,000**
- recorded elapsed: **120.8 ms**
- recorded rate: **86.424 million channel evaluations/s**
- render stress: **29,000 instances × 30 frames**
- recorded frame time: **18.497 ms/frame**
- equivalent rate: **54.06 FPS**
- exact original-view replay: **PASS**
- alternate view differs: **PASS**
- exact time replay: **PASS**

**Claim ceiling:** procedural state comparison is not a universal video-codec compression claim.

## 9. Gate24 Glass Box initiation

The browser integration ran twelve isolated Orphanim workcells over the same public tasks.

- earned gates: **24 / 24**
- holds: **0**
- parallel workcell latency: **1.6 ms**
- serial latency: **4.3 ms**
- measured serial/parallel ratio: **2.687×**
- semantic roots equal: **true**
- pre-cycle workers reaped: **12 → 0**
- experiment workers cleaned: **12 → 0**

**Claim ceiling:** these were browser Workers running tiny deterministic tasks, not twelve independent LLM minds. Lower latency is not evidence of better reasoning quality.

## 10. C++ 100-cycle 4→3→4→3 scheduler

This run is important because it produced a **negative finding**, not just a PASS.

- requested cycles: **100**
- closed cycles: **100**
- HOLD cycles: **0**
- phase executions: **400 / 400 PASS**
- Gate24 rebases: **100 / 100**
- gate receipts: **2,400 / 2,400**
- semantic-equivalent rebases: **100 / 100**
- constitutional commits: **100 / 100**
- distinct Witness roots: **100**
- wall time: **18.341 s**
- workers after cleanup: **0**

But the run discovered that the then-current judge was too permissive: procedural Gate24 closure could reuse program-level acceptance evidence even when a named physical feature had not actually been materialized.

Therefore the correct disposition was:

`PASS_SCHEDULER_AND_RECURSIVE_CLOSURE / HOLD_NORTH_STAR_PHYSICAL_COMPLETION`

**Keeper:** `ProceduralGate24Closure != PhysicalFeatureCompletion`.

## 11. Corrected North-Star physical convergence

The judge was repaired with residual-specific physical canaries and rerun from fresh state.

- theoretical reciprocal minimum: **25 residuals × 2 = 50 closures**
- physical closures: **50 / 50**
- cycles executed: **51**
- extra HOLD cycles: **1**
- repair actions: **12**
- hard HOLD: **false**
- elapsed: **318.136 s**
- exported seed: **6,292,160 bytes**
- embedded L0–L3 corpus: **23 documents**
- stripped private L4 locators: **481**
- live Drive/Docs pointers in public seed: **0**
- Memory City: **23 buildings / 17 districts**
- leased siblings: **12 unique runtime IDs / 12 unique leases**
- zero-orphan final state: **PASS**
- constitutional generation: **50 committed deltas**
- final physical status: `PASS_NORTH_STAR_PHYSICAL`

The one additional cycle occurred because only 2 of 12 leased siblings were immediately READY. The gate correctly held; the next cycle observed 12/12 READY and closure proceeded.

A prior parser could mistake a nested child READY for parent PASS. That run was rejected as non-canonical and the corrected run was restarted.

**Keeper:** `NestedReady != ParentCanaryPass`.

## 12. Four-parent 51×4 dimensional lift

Four sovereign parents each ran **51 cycles**:

- P1 embodied witness
- P2 knowledge reopen
- P3 recursive privacy
- P4 portable governance

Total parent cycles: **204**.

The first four-parent child produced `HOLD_GATE24_INCOMPLETE` with only **1 / 24** gates because ancestry roots alone did not carry gate-specific reproducible evidence. That failed child was preserved.

A repaired parent-evidence cartridge then supplied the required acceptance evidence:

- repaired child Gate24: **24 / 24**
- candidate lifecycle: create → prove → witness → promote
- final cleanup: `PASS_ZERO_OWNED_DESCENDANTS`
- final child disposition: `PASS_OMNI_CHILD`

**Keeper:** ancestry does not imply admission.

## 13. Archangel neural before/after A/B

Rendered V5 Arena A/B test:

- pairs: **12**
- pre states: **24**
- post states: **24**
- total measured states: **48**
- clean-pair median speedup: **3.4909×**
- clean-pair geometric mean: **3.0253×**
- heavy-touch reduction: **75%**
- invalid-boundary attempts: **12**
- invalid-boundary leakage: **0**
- fault-boundary leakage: **0**
- stall cases: **12**
- fail-stop cases: **12**
- corruption cases: **12**
- final status: `PASS_AB_ARCHANGEL_NEURAL`

A forced mixed-mode fallback test also passed, demonstrating graceful degradation rather than requiring all 12 lanes to remain in the optimized mode.

## 14. H01 selective brain reification

Computational scaling fixture:

- procedural neurons: **64,000**
- procedural synapse addresses: **150,000,000**
- touched neurons: **5,714**
- touched synapses: **318,420**
- touched synapse fraction: **0.0021228 = 0.21228%**
- effective sparse synapse storage: **5,094,720 bytes**
- monolithic 64-bit synapse baseline: **1,200,000,000 bytes**
- measured reduction vs monolithic baseline: about **235.54×**
- canary status: `PASS_H01_SELECTIVE_BRAIN_REIFICATION`

**Claim ceiling:** a procedural/sparse computational brain fixture is not a biological brain simulation.

## 15. Virtual photonic lineage memory

Exact source-pair experiment over parent V5 HTML and a mutated child:

- parent bytes: **54,612,970**
- child bytes: **54,612,970**
- exact patch bytes: **21,570**
- changed 64 KiB chunks: **2 / 834**
- child reopen exact: **true**
- patch reapply exact: **true**
- incremental ratio vs full duplicate: **0.00039497**
- incremental saving vs duplicating child: **99.9605%**
- full-copy / patch ratio: **2,531.9×**
- separate hot virtual-memory artifact: **24,393 bytes**
- status: `PASS_EXACT_LINEAGE_CRYSTAL`

**Claim ceiling:** this is virtual/algorithmic lineage memory, not a fabricated photonic storage device.

## 16. ARIEL recursive-journey fuzzing

The navigation/story/worldline harness was exercised for **51 journeys**:

- journeys completed: **51**
- generation: **51**
- total receipts: **417**
- free-form routes: **41**
- unique stations visited: **23**
- final current station: `one_prime`
- live Knowledge Genome witness statuses: **414**
- unresolved route-endpoint nominations were retained as typed HOLDs instead of silently becoming valid routes

This is a robustness/navigation receipt benchmark, not a throughput benchmark.

---

## What should reproduce exactly vs vary

### Expected to reproduce exactly

- invariant/correctness PASS/HOLD conditions
- deterministic roots where the same deterministic fixture and implementation are used
- address round trips and mirror involutions
- transpose/reopen equality
- structural pair counts for a fixed schedule
- zero-leakage / exact-reopen assertions

### Expected to vary by machine

- wall-clock milliseconds
- operations per second
- browser FPS equivalents
- heap/RSS behavior
- parallel/serial latency ratios

When comparing performance, record compiler, flags, CPU, OS, browser version, and whether the Arena/WebGL carrier was active.

## Claim boundaries

These benchmarks test **software structures, deterministic kernels, simulations, browser runtime behavior, and declared fixtures**.

They do not by themselves establish:

- consciousness or subjective experience;
- physical higher-dimensional worlds;
- a physical quantum computer or generic quantum advantage;
- a physical photonic memory device;
- a biological brain simulation;
- universal media compression;
- universal reasoning-quality gains from parallelism or scheduling geometry.

The intended rule is:

```text
PASS means the declared fixture passed.
HOLD means the evidence was insufficient or a boundary failed.
Neither should be widened into a stronger claim without a new matched test.
```
