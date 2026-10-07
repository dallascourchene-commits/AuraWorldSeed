# Prove the AuraWorldSeed benchmarks yourself

This guide is for an independent reviewer who does **not** want to trust precomputed Aura receipts.

The goal is to make the important distinction visible:

```text
WITHOUT / control  ->  WITH / treatment  ->  measured delta  ->  claim ceiling
```

Not every benchmark is a performance comparison. Some are correctness, persistence, or falsification tests. Where no honest matched baseline exists, the documentation says so explicitly.

## Route A — easiest independent proof: fork and run on GitHub

This is the cleanest route if you do not want to install a compiler locally.

1. Fork `dallascourchene-commits/AuraWorldSeed` into **your own GitHub account**.
2. Open your fork.
3. Open **Actions**.
4. Enable workflows if GitHub asks.
5. Select **Reproduce Core Aura Benchmarks**.
6. Click **Run workflow**.
7. Choose the number of repetitions. Start with **3**; use **5–20** for stronger timing evidence.
8. Open the completed job and inspect the log.
9. Download the **fresh-benchmark-receipts** artifact.
10. Open `COMPARISON.md`, `ENVIRONMENT.json`, and the raw JSON receipts.

Why a fork matters: the code still comes from this public repository, but **the execution is initiated from your account and runs on GitHub's runner**, not on the author's computer and not from a supplied ZIP.

Workflow:

https://github.com/dallascourchene-commits/AuraWorldSeed/actions/workflows/reproduce-benchmarks.yml

## Route B — run on your own machine

Requirements:

- Python 3.10+
- a C++20-capable `g++`
- Git if cloning the repository

Clone and inspect first:

```bash
git clone https://github.com/dallascourchene-commits/AuraWorldSeed.git
cd AuraWorldSeed
git rev-parse HEAD
git status --short
```

Then run:

```bash
python3 benchmarks/reproduce.py --repeats 5
```

On Windows with the Python launcher:

```powershell
py benchmarks\reproduce.py --repeats 5
```

Fresh evidence is written under:

```text
benchmark-results/
  ENVIRONMENT.json
  COMPARISON.md
  *_run01.json
  *_run02.json
  ...
```

The script compiles the C++ sources from the repository itself. It does not read benchmark answers from the developer package.

## Route C — browser-only 24³ closure

Open:

https://dallascourchene-commits.github.io/AuraWorldSeed/benchmarks/24cube.html

The browser kernel executes the 24×24×24 closure locally.

The published deterministic closure root is:

```text
b54707b90f015a0b8318ae953ebe26907e8f552e6eaea5e48da68fc597facab4
```

The important correctness checks are 13,824 unique work receipts/addresses/objectives, exact address round trips, mirror involutions, receipt-chain verification, six typed HOLD→repair→resume paths, and zero unresolved required HOLDs.

## What the standalone reproducer compares

### Triad/quartet schedule

**WITHOUT:** fixed static grouping.

**WITH:** pinned balanced rotating 3-person / 4-person lattice.

The same program emits the fixed control, a deterministic fastest-search result, and the historical balanced reference in one receipt. The balanced reference is not accepted because an old JSON says so: the public evaluator recomputes all of its pair counts and invariants from the pinned schedule. The key structural comparison is:

```text
fixed static:       30 / 66 unique pairs
balanced reference: 66 / 66 unique pairs
```

It also reports pair-count imbalance, role balance, early coverage, and 100-world-scale structural persistence.

### HDC / VSA

**WITHOUT:** direct O(D²) circular-convolution reference.

**WITH:** FFT HRR, plus a cached-spectrum HRR path.

Both reference and optimized path are evaluated by the same executable on the same machine. The script computes a fresh per-run speed ratio.

The correctness guard is equally important: the FFT result must agree with the direct reference to the declared numerical tolerance. A faster wrong result does not count.

### Exact reification

**WITHOUT:** store the full source bytes.

**WITH:** exact program + residual representation.

The reproducer generates two controls:

- a highly structured 128 KiB fixture where reification should win;
- a deterministic pseudo-random 128 KiB negative control where it should **not** invent a compression win.

Both must reopen byte-exactly.

This negative control is intentional. A representation method that only reports favorable compressible examples is not a convincing benchmark.

### 3×4 ↔ 4×3 projection

This is mainly a **correctness/invertibility** benchmark, not a performance A/B.

It performs 1,000,000 transpose/reopen trials and requires zero state/root mismatches. It also preserves a scalar-aggregation collision as the negative counterexample to flattening reconstructable components into one scalar.

### Orphanim 24⁴

This is a deterministic structural-throughput/correctness test.

There is **no matched performance baseline currently claimed** in the standalone suite. The historical JavaScript timeout and the native C++ result used different execution implementations/carriers, so they should not be treated as a clean scientific A/B.

The standalone claim is limited to its own deterministic invariants and measured throughput.

## Historical Arena paired controls

These are documented in `benchmarks/README.md`. They are not all part of the small standalone runner because they require the rendered World Seed/browser integration.

### Gate24 workcells

```text
WITHOUT parallelism: serial     4.3 ms
WITH parallelism:               1.6 ms
same semantic root:             true
measured ratio:                 2.687×
```

The workload was tiny deterministic browser-worker work. This is a latency result, not a reasoning-quality result.

### Archangel neural A/B

```text
WITHOUT neural dispatch path: pre condition
WITH neural dispatch path:    post condition
pairs:                         12
median clean-pair speedup:     3.4909×
geometric mean speedup:        3.0253×
heavy-touch reduction:         75%
boundary leakage:              0
```

### H01 selective computational-brain fixture

```text
WITHOUT selective manifestation:
  monolithic 64-bit synapse-address baseline = 1,200,000,000 bytes

WITH consequence-local manifestation:
  effective sparse synapse storage = 5,094,720 bytes

storage-accounting ratio ≈ 235.54×
touched synapses = 318,420 / 150,000,000 = 0.21228%
```

This is a computational scaling fixture, not a biological-brain claim.

### Lineage patch vs full duplicate

```text
WITHOUT lineage delta:
  duplicate full child = 54,612,970 bytes

WITH exact lineage patch:
  patch = 21,570 bytes

incremental ratio = 0.00039497
incremental saving = 99.9605%
full-copy / patch = 2,531.9×
exact child reopen = PASS
```

This is algorithmic storage/lineage evidence, not a physical photonic-device result.

### Four-parent lift validity control

This is a correctness A/B rather than a speed test.

```text
WITHOUT gate-specific parent evidence:
  Gate24 = 1 / 24
  status = HOLD_GATE24_INCOMPLETE

WITH explicit reproducible parent-evidence cartridge:
  Gate24 = 24 / 24
  status = PASS_OMNI_CHILD
```

That failed first child is retained as the falsifier.

### Physical-canary judge repair

Again, this is a **validity** comparison rather than a speedup claim.

The old judge closed 100/100 procedural cycles but could not justify the stronger physical-feature conclusion.

After residual-specific physical canaries were added:

```text
50 / 50 reciprocal physical closures
51 cycles
1 real HOLD
12 repairs
hard HOLD = false
final = PASS_NORTH_STAR_PHYSICAL
```

The point is that the corrected judge became harder to satisfy, not faster.

### 24³ closed-world vs full Arena carrier

Same 24³ kernel, same 24 repetitions:

```text
closed-world mean:  744.8 ms
9D Arena mean:      787.1 ms
```

The integrated carrier was about 5.7% slower on this historical run and accumulated scene/AEV state. That negative overhead is published because controls should expose costs as well as wins.

## Effect size is not automatically statistical significance

The repository uses the word **effect** for measured differences unless the experimental design supports a stronger statistical statement.

For timing claims:

1. use the same machine and compiler for baseline and treatment;
2. run baseline and treatment in the same executable where possible;
3. use at least **5 repetitions** for a basic sanity check;
4. use **10–20 repetitions** if you want a more convincing timing distribution;
5. report median and spread, not only the best run;
6. do not change the fixture, compiler flags, workload size, or correctness criterion between conditions;
7. reject any speedup if correctness diverges.

A p-value is not automatically meaningful for deterministic microbenchmarks with machine-noise repetitions. Effect size, paired design, variance, exact correctness, and independent reruns are often more informative. If a formal inferential test is used, the raw repeated measurements should be published with it.

## How to try to falsify the result

Independent reproduction is stronger when you actively try to break it.

Good falsification attempts include:

- increase `--repeats`;
- change the triad/quartet random seed;
- increase the search iterations;
- compile without `-march=native`;
- run on a different CPU/OS;
- inspect and alter the structured/random reification controls;
- run the HDC executable under its stricter literal-orthogonality policy;
- verify that correctness guards fail when you deliberately corrupt an output/root;
- compare your raw JSON rather than relying on README prose.

If a claimed invariant fails, preserve the failing receipt. That is evidence, not something to hide.

## What should match exactly

These should normally match under the same fixture/implementation:

- deterministic roots;
- pair counts for a fixed schedule;
- address and mirror round trips;
- exact-reopen checks;
- transpose/reopen equality;
- PASS/HOLD correctness conditions.

These normally vary:

- milliseconds;
- operations/second;
- FPS;
- heap/RSS;
- parallel/serial timing ratios.

Always publish the environment alongside performance numbers.
