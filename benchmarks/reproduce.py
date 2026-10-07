#!/usr/bin/env python3
"""Independent core benchmark reproducer for AuraWorldSeed.

Compiles the public C++20 benchmark sources, runs paired/control fixtures,
checks deterministic invariants, and writes fresh JSON receipts plus a
human-readable comparison summary. No developer ZIP is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import shutil
import statistics
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "benchmarks" / "src"

SOURCES = {
    "orphanim24": "orphanim_24pow4_bench.cpp",
    "triadquartet": "triad_quartet_lattice_bench.cpp",
    "projection": "triad_quartet_projection_unification_bench.cpp",
    "hdc": "hdc_dual_frontier_bench.cpp",
    "reification": "reification_frontier_microscope.cpp",
}


def run(cmd: list[str], *, cwd: pathlib.Path = ROOT, allow_codes: set[int] = {0}) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), flush=True)
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if p.stdout:
        print(p.stdout.rstrip(), flush=True)
    if p.stderr:
        print(p.stderr.rstrip(), file=sys.stderr, flush=True)
    if p.returncode not in allow_codes:
        raise SystemExit(f"command failed with exit code {p.returncode}: {' '.join(cmd)}")
    return p


def write_json_stdout(proc: subprocess.CompletedProcess[str], path: pathlib.Path) -> dict[str, Any]:
    path.write_text(proc.stdout, encoding="utf-8")
    try:
        return json.loads(proc.stdout)
    except Exception as exc:
        raise SystemExit(f"{path.name}: output was not valid JSON: {exc}") from exc


def median(values):
    return statistics.median(values) if values else float("nan")


def pct_change(new: float, old: float) -> float:
    return ((new - old) / old) * 100.0 if old else float("inf")


def make_fixtures(fixtures: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    fixtures.mkdir(parents=True, exist_ok=True)
    structured = fixtures / "structured_128k.bin"
    randomish = fixtures / "deterministic_random_128k.bin"

    pattern = b"AURA|L0-L1-L2-L3|REOPEN|GATE24|0123456789ABCDEF\n"
    structured.write_bytes((pattern * ((131072 // len(pattern)) + 1))[:131072])

    blocks = []
    i = 0
    while sum(map(len, blocks)) < 131072:
        blocks.append(hashlib.sha256(f"AURA-NEGATIVE-CONTROL-{i}".encode()).digest())
        i += 1
    randomish.write_bytes(b"".join(blocks)[:131072])
    return structured, randomish


def main() -> int:
    ap = argparse.ArgumentParser(description="Reproduce AuraWorldSeed standalone core benchmarks.")
    ap.add_argument("--repeats", type=int, default=3, help="Timed repetitions per benchmark (default: 3).")
    ap.add_argument("--iterations", type=int, default=1_000_000, help="Triad/quartet candidate schedules per repetition.")
    ap.add_argument("--seed", type=int, default=20261006, help="Triad/quartet deterministic search seed.")
    ap.add_argument("--out", default="benchmark-results", help="Output directory.")
    args = ap.parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats must be >= 1")

    out = ROOT / args.out
    bin_dir = out / "bin"
    fixtures = out / "fixtures"
    out.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    structured, randomish = make_fixtures(fixtures)

    cxx = shutil.which("g++")
    if not cxx:
        raise SystemExit("g++ not found. Install a C++20-capable GCC/G++ or use the GitHub Actions workflow.")

    flags = ["-O3", "-march=native", "-std=c++20"]
    ext = ".exe" if os.name == "nt" else ""
    executables: dict[str, pathlib.Path] = {}
    for name, source in SOURCES.items():
        exe = bin_dir / f"{name}{ext}"
        run([cxx, *flags, str(SRC / source), "-o", str(exe)])
        executables[name] = exe

    env = {
        "platform": platform.platform(),
        "python": sys.version,
        "compiler": run([cxx, "--version"]).stdout.splitlines()[0],
        "compiler_flags": " ".join(flags),
        "repeats": args.repeats,
        "triad_iterations": args.iterations,
        "triad_seed": args.seed,
        "git_commit": None,
    }
    git = shutil.which("git")
    if git:
        p = subprocess.run([git, "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True)
        if p.returncode == 0:
            env["git_commit"] = p.stdout.strip()
    (out / "ENVIRONMENT.json").write_text(json.dumps(env, indent=2), encoding="utf-8")

    all_runs: dict[str, list[dict[str, Any]]] = {k: [] for k in SOURCES}
    for rep in range(1, args.repeats + 1):
        tag = f"run{rep:02d}"

        p = run([str(executables["orphanim24"])])
        d = write_json_stdout(p, out / f"orphanim_24pow4_{tag}.json")
        assert d["status"] == "PASS_24POW4_ORPHANIM"
        assert d["logical_coordinates"] == 24**4
        assert d["rank_roundtrip_pass"] == 24**4
        assert d["mirror_involution_pass"] == 24**4
        assert d["semantic_invariant_pass"] == (24**4) * 24
        all_runs["orphanim24"].append(d)

        p = run([str(executables["triadquartet"]), str(args.iterations), str(args.seed)])
        d = write_json_stdout(p, out / f"triad_quartet_{tag}.json")
        assert d["search_iterations"] == args.iterations
        assert d["fixed_static_grid"]["unique_pairs"] == 30
        assert d["best"]["metrics"]["operational_position_unique"] is True
        assert d["best"]["metrics"]["unique_pairs"] == 66
        assert d["world_scale_test"]["all_structural_invariants"] is True
        all_runs["triadquartet"].append(d)

        p = run([str(executables["projection"])])
        d = write_json_stdout(p, out / f"projection_unification_{tag}.json")
        assert d["transpose_reopen"]["trials"] == 1_000_000
        assert d["transpose_reopen"]["state_mismatches"] == 0
        assert d["transpose_reopen"]["root_mismatches"] == 0
        assert d["sovereignty_counterexample"]["scalar_aggregation_collision"] is True
        all_runs["projection"].append(d)

        p = run([str(executables["hdc"]), "--statistical-orthogonality"])
        d = write_json_stdout(p, out / f"hdc_vsa_{tag}.json")
        assert d["disposition"] == "PASS"
        assert d["falsifiers"]["HRR_FFT_REFERENCE"] == "PASS"
        all_runs["hdc"].append(d)

        p = run([
            str(executables["reification"]),
            str(structured.relative_to(ROOT)),
            str(randomish.relative_to(ROOT)),
            "README.md",
        ])
        d = write_json_stdout(p, out / f"reification_{tag}.json")
        assert d["disposition"] == "PASS_EXACT_REOPEN_MICROSCOPE"
        assert all(x["exact_reopen"] for x in d["files"])
        by_name = {pathlib.Path(x["path"]).name: x for x in d["files"]}
        assert by_name[structured.name]["exact_ratio"] < 0.10
        assert by_name[randomish.name]["exact_ratio"] > 0.95
        all_runs["reification"].append(d)

    tq = all_runs["triadquartet"][0]
    fixed = tq["fixed_static_grid"]
    best = tq["best"]["metrics"]
    fixed_cov = fixed["unique_pairs"] / 66 * 100.0
    best_cov = best["unique_pairs"] / 66 * 100.0
    imbalance_reduction = (1.0 - best["pair_stddev"] / fixed["pair_stddev"]) * 100.0

    hdc_full_ratios = []
    hdc_cached_ratios = []
    for d in all_runs["hdc"]:
        direct_ms = d["evidence"]["direct_d2_reference_elapsed_ms"]
        full_ms = 1000.0 / d["benchmarks"]["hrr"]["bind_throughput_ops_sec"]
        cached_ms = 1000.0 / d["benchmarks"]["hrr"]["bind_cached_spectral_ops_sec"]
        hdc_full_ratios.append(direct_ms / full_ms)
        hdc_cached_ratios.append(direct_ms / cached_ms)

    r0 = all_runs["reification"][0]
    rb = {pathlib.Path(x["path"]).name: x for x in r0["files"]}
    rs = rb[structured.name]
    rr = rb[randomish.name]
    structure_factor = rs["source_bytes"] / rs["best_exact_bytes"]

    orph_tp = median([d["million_semantic_frames_per_sec"] for d in all_runs["orphanim24"]])
    projection_sec = median([d["transpose_reopen"]["seconds"] for d in all_runs["projection"]])

    summary = f"""# Fresh comparison summary

Generated by `benchmarks/reproduce.py` from **{args.repeats} fresh run(s)** on this machine.

| Test | WITHOUT / control | WITH / treatment | Fresh effect |
|---|---:|---:|---:|
| Triad/quartet pair coverage | fixed static: {fixed["unique_pairs"]}/66 ({fixed_cov:.1f}%) | searched balanced schedule: {best["unique_pairs"]}/66 ({best_cov:.1f}%) | +{best_cov-fixed_cov:.1f} percentage points; pair-count SD {imbalance_reduction:.1f}% lower |
| HDC HRR binding | direct O(D²) reference | FFT HRR | median **{median(hdc_full_ratios):.1f}×** faster on this carrier |
| HDC cached HRR binding | direct O(D²) reference | cached-spectrum HRR | median **{median(hdc_cached_ratios):.1f}×** faster on this carrier |
| Exact reification, structured negative/control pair | full source: {rs["source_bytes"]:,} bytes | exact program+residual: {rs["best_exact_bytes"]:,} bytes | **{structure_factor:.1f}×** smaller while exact-reopen passes |
| Reification negative control | deterministic random source: {rr["source_bytes"]:,} bytes | best exact representation: {rr["best_exact_bytes"]:,} bytes | ratio **{rr["exact_ratio"]:.4f}** — correctly shows no compression win |

Additional fresh checks:
- Orphanim 24⁴: all deterministic invariants PASS; median throughput **{orph_tp:.3f} million semantic frames/s**. No matched performance baseline is claimed for this test.
- 3×4↔4×3 projection: 1,000,000 transpose/reopen trials, 0 state/root mismatches; median **{projection_sec:.6f} s**. The scalar-aggregation collision is a correctness counterexample, not a speed baseline.

## Interpretation

A large ratio is an **effect size on this declared fixture and carrier**, not automatically a universal or statistically significant claim. For timing claims, increase `--repeats` (5–20 is useful), keep baseline and treatment on the same machine/run, and report the distribution rather than one lucky number.

The structured + random reification pair is intentionally important: a valid method should win where structure exists **and refuse to invent a win on incompressible-looking input**.
"""
    (out / "COMPARISON.md").write_text(summary, encoding="utf-8")
    print(summary)

    print(f"PASS: all core assertions held across {args.repeats} repetition(s).")
    print(f"Fresh receipts: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
