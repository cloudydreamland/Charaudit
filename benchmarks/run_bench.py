"""Reproducible performance benchmarks for charaudit (stdlib only, seeded).

Methodology (stated up front, no cherry-picking):
- Samples are SYNTHETIC, generated deterministically with random.Random(20261008)
  from fixed character pools (common CJK characters, ASCII, planted invisible
  and homoglyph characters). They are not real-world corpora.
- Every measurement wraps a fixed number of calls with time.perf_counter and
  reports best and median of REPEATS runs, on the machine recorded in
  RESULTS.md. Timings vary between machines and runs; numbers are only
  comparable to themselves.

Usage:
    cd /path/to/charaudit
    PYTHONPATH=src python benchmarks/run_bench.py
"""
from __future__ import annotations

import os
import platform
import statistics
import sys
import time
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from charaudit import audit_text, diff_visible, sanitize  # noqa: E402

SEED = 20261008
REPEATS = 5

CJK_POOL = "的一是不了人我在有他这中大来上国和地到时要说就也对出点会成只可事物体用生发作自家己已末未土士王玉"
ASCII_POOL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:;?!()\"'-"
PLANTED = ["\u200b", "\u0435", "\u00ad", "\u2060"]  # ZWSP, Cyrillic е, soft hyphen, WORD JOINER


def make_sample(rng, target_len: float, cjk_ratio: float, plant_every: int) -> str:
    parts: list[str] = []
    for i in range(int(target_len)):
        if i % plant_every == plant_every - 1:
            parts.append(rng.choice(PLANTED))
        elif rng.random() < cjk_ratio:
            parts.append(rng.choice(CJK_POOL))
        else:
            parts.append(rng.choice(ASCII_POOL))
    return "".join(parts)


def build_samples() -> dict[str, str]:
    rng = __import__("random").Random(SEED)
    return {
        "prompt-short (~120 chars, mixed, planted)": make_sample(rng, 120, 0.4, 30),
        "doc-medium (~6k chars, mixed, planted)": make_sample(rng, 6000, 0.5, 200),
        "cjk-dense (~60k chars, planted)": make_sample(rng, 60000, 0.95, 500),
    }


def bench(label: str, func, *args, repeats: int = REPEATS, **kwargs) -> dict:
    times: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        func(*args, **kwargs)
        times.append(time.perf_counter() - start)
    best = min(times)
    median = statistics.median(times)
    n_chars = len(args[0])
    return {
        "label": label,
        "best_ms": best * 1000.0,
        "median_ms": median * 1000.0,
        "best_chars_per_s": n_chars / best if best > 0 else float("inf"),
    }


def main() -> None:
    samples = build_samples()
    print("== charaudit benchmark ==")
    print(f"python     : {sys.version.split()[0]} ({platform.architecture()[0]})")
    print(f"platform   : {platform.platform()}")
    print(f"processor  : {os.environ.get('PROCESSOR_IDENTIFIER') or platform.processor() or 'unknown'}")
    print(f"unicodedata: {unicodedata.unidata_version}")
    print(f"method     : best/median of {REPEATS} runs per cell, time.perf_counter, seeded samples (seed={SEED})")
    print()

    rows: list[dict] = []
    for name, text in samples.items():
        pair = text + "!"  # one visible difference for diff_visible
        rows.append(bench(f"audit_text strict   | {name}", audit_text, text, policy="strict"))
        rows.append(bench(f"audit_text neutral | {name}", audit_text, text, policy="neutral"))
        rows.append(bench(f"sanitize strict    | {name}", sanitize, text))
        rows.append(bench(f"diff_visible       | {name}", diff_visible, text, pair))

    width = max(len(r["label"]) for r in rows)
    print(f"{'operation / sample'.ljust(width)}  best(ms)  median(ms)  best chars/s")
    for r in rows:
        print(
            f"{r['label'].ljust(width)}  {r['best_ms']:8.2f}  {r['median_ms']:10.2f}  {r['best_chars_per_s']:12,.0f}"
        )
    print()
    print("findings per sample (strict):")
    for name, text in samples.items():
        report = audit_text(text, policy="strict")
        print(f"  {name}: {len(report.findings)} findings, stats={report.stats()}")


if __name__ == "__main__":
    main()
