# Virtual Memory Crystal (VMC) benchmark ledger

These results were originally run on **2026-09-17 through 2026-09-18** and were omitted from the Oct. 6–7 benchmark harvest because they fell outside that time window. They are now part of the public benchmark corpus.

The original executable Python sources are mirrored here:

- [VMC-001 source](src/vmc_virtual_memory_crystal_v01.py)
- [VMC-002 source](src/vmc002_rubik_proof_crystal.py)

A dedicated GitHub Actions workflow reproduces both from source:

- [Reproduce Virtual Memory Crystal](https://github.com/dallascourchene-commits/AuraWorldSeed/actions/workflows/reproduce-vmc.yml)

**Verified fresh public run:** [GitHub Actions run #37610839443](https://github.com/dallascourchene-commits/AuraWorldSeed/actions/runs/37610839443) completed successfully in 29 seconds. On that runner, VMC-002 measured **35.9258×** on the structured quotient/local-consequence fixture and **0.9475×** on the high-entropy negative control; VMC-001 reproduced the **13.9161%** E8 MSE reduction.

## Headline results

| Test | WITHOUT / control | WITH / VMC treatment | Measured result | Correctness / boundary |
|---|---:|---:|---:|---|
| **VMC-002 exact quotient × local consequence** | full baseline: **753.612 ms** | exact quotient/local route: **21.027 ms** | **35.840× faster** | exact outputs = true |
| **VMC-002 high-entropy negative control** | baseline: **275.872 ms** | cached/quotient route: **280.153 ms** | **0.9847×** (slightly slower) | exact outputs = true; correctly shows no universal win |
| **VMC-001 E8 vs Z8 quantization** | Z8 MSE/dim **0.08332172** | E8 MSE/dim **0.07172657** | **13.92% lower MSE** | 120,000 samples; E8 membership 100% |
| **VMC-001 low-noise decode** | Z8 error **4.3158%** at σ=0.18 | E8 error **0.7875%** | **81.75% relative decode-error reduction** | same noise fixture |
| **VMC + AuraZip HOT descriptor** | whole Arena **1,013,894 B** | HOT descriptor **349 B** | **99.96558% smaller active descriptor** | this is selective hydration, not whole-file compression |
| **VMC-first exact reopen** | ordinary full-file reopen path is not claimed as a matched timing baseline | encrypted 16×64 KiB WORM pages | **100 reopens mean ≈14.1 ms; p95 ≈18.5 ms** | exact whole-Arena reopen; 5,000 bit flips, 0 accepted |

## 1. VMC-002: exact quotient × local consequence

This is the strongest VMC performance result.

Declared fixture:

- logical instances: **B = 128**
- exact execution classes: **Q = 16**
- full consequence width: **F = 27**
- local consequence width: **D = 6**
- structural fraction: `(Q/B) × (D/F) = 0.0277778`
- ideal pre-overhead speedup: **36×**

Measured same-program result:

```text
WITHOUT / full baseline:       753.611695 ms
WITH / quotient+local route:    21.026922 ms
measured speedup:               35.8403239×
exact outputs:                  true
```

That is close to the declared 36× structural ideal.

### Required negative control

The benchmark also generated a high-entropy case where every logical instance was effectively unique:

```text
B = 48
Q = 48

baseline: 275.871995 ms
cached:   280.152612 ms
speedup:  0.984720×
exact:    true
```

This negative control matters. When exact execution equivalence disappears, the optimization produces **no speedup and is slightly slower**. Therefore the earned claim is not “VMC makes everything 35.8× faster.” It is:

> **Exact duplicate execution classes × local consequence reduction can produce a large measured win when the fixture actually contains that structure; high-entropy unique work does not.**

## 2. VMC-001: E8 coding improvement

At equal lattice scale over **120,000 8D samples**:

```text
Z8 MSE / dimension = 0.0833217245
E8 MSE / dimension = 0.0717265694
reduction          = 13.9161%
E8 membership      = 100%
```

Noise-decode comparison:

| Gaussian σ | Z8 error | E8 error | Relative error reduction |
|---:|---:|---:|---:|
| 0.18 | 4.3158% | 0.7875% | **81.75%** |
| 0.24 | 26.0808% | 15.4192% | **40.88%** |
| 0.30 | 55.3642% | 46.1758% | **16.60%** |
| 0.36 | 76.5083% | 71.6658% | **6.33%** |
| 0.42 | 88.1858% | 86.1917% | **2.26%** |

The benefit narrows as noise becomes extreme, which is exactly the kind of degradation curve a useful benchmark should expose.

The same VMC-001 experiment also retained a falsifier: a rank-5 continuous **8D→5D** projection lost **37.41% of input variance** even with no added noise. Therefore the result explicitly rejects a naive “lossless 8D into five continuous optical parameters” claim.

## 3. VMC persistence / damage tests

VMC-001 exact persistence:

- **32/32** initial page reads exact
- **32/32** reads exact after close/reopen
- overwrite of an existing WORM page rejected
- one-byte corruption detected by content roots

For the moderate single-layer-dropout optical fixture, parity recovery produced **192/192 exact pages** for the tested 1-, 2-, and 4-bit-per-voxel lanes.

This is software-channel and archive evidence, not proof of a fabricated physical glass device.

## 4. VMC + AuraZip selective retrieval

Historical current-Arena canary:

- Arena: **1,013,894 bytes**
- VMC: **16 × 65,536-byte pages**
- semantic sections: **43**
- HOT descriptor: **349 bytes**
- full semantic-index manifest: **10,942 bytes**
- default maximum first hydration: **8,192 bytes**
- descriptor reduction vs full Arena: **99.96558%**
- random exact-byte campaign: **10,000 / 10,000 exact**
- 1,000 random 4 KiB mutations: median **1** changed 64 KiB page; maximum **2**

This is a **working-set / hydration reduction**, not a claim that the 1 MB source was compressed into 349 bytes. The whole source remains available through exact reopen.

## 5. VMC-first whole-Arena seal / reopen

A later VMC-first successor test sealed an approximately **1,005,087-byte** Arena into **16 × 64 KiB encrypted WORM logical pages**.

Measured reference-environment result:

- seal: approximately **68.4 ms**
- 100 exact reopens: mean approximately **14.1 ms**
- p95 reopen: approximately **18.5 ms**
- **5,000** randomized ciphertext bit flips: **0 accepted**
- exact whole-Arena reopen: **PASS**

This is a persistence/integrity result. No physical crystal hardware, hardware cryptographic module, or device-key binding is implied.

## Reproduce it yourself

### GitHub

Open:

**Actions → Reproduce Virtual Memory Crystal → Run workflow**

The workflow installs the declared Python dependencies and runs the original VMC-001 and VMC-002 sources mirrored above.

### Local

Requirements:

```bash
python -m pip install numpy scipy scikit-learn
```

Then:

```bash
sudo mkdir -p /mnt/data
sudo chmod 777 /mnt/data

python benchmarks/src/vmc_virtual_memory_crystal_v01.py
python benchmarks/src/vmc002_rubik_proof_crystal.py
```

The original sources use `/mnt/data/` for their output directories because that was the benchmark carrier used when they were written.

## Claim boundary

The VMC experiments establish results about:

- deterministic software WORM archives;
- exact reopen/integrity;
- reduced optical-channel and scalar angular-spectrum simulations;
- finite E8 coding;
- exact execution quotienting;
- local-consequence evaluation;
- selective hydration.

They do **not** establish:

- a fabricated physical optical/glass memory device;
- measured physical photonic throughput;
- a new cryptographic primitive;
- universal 35.84× acceleration;
- lossless arbitrary continuous 8D→5D projection;
- universal whole-file compression.

The high-entropy negative control is part of the benchmark precisely to prevent the 35.84× result from being widened beyond the structured regime where it was earned.
