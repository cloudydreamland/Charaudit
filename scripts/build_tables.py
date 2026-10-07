"""Build the packaged homoglyph data tables from auditable sources.

Inputs (both committed to the repository for the audit chain):
- data/raw/confusables.txt      Unicode confusables.txt (UTS #39 security data)
- data/cjk_confusables.json     hand-curated CJK near-homograph groups

Outputs (what the package actually ships):
- src/charaudit/data/confusables_un.json
- src/charaudit/data/cjk_confusables.json

Every output embeds a ``_meta`` block: source URL, version, raw-file SHA-256,
the exact filter/curation rule, per-stage counts, and ``map_sha256`` — the
SHA-256 of the canonical JSON of the mapping itself (see tests). Output is
byte-deterministic: sorted keys, compact separators, no timestamps beyond the
recorded download/curation dates.

Usage:
    python scripts/build_tables.py \
        --raw data/raw/confusables.txt \
        --cjk data/cjk_confusables.json \
        --out src/charaudit/data
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

LINE_RE = re.compile(r"^([0-9A-Fa-f][0-9A-Fa-f ]*)\s*;\s*([0-9A-Fa-f][0-9A-Fa-f ]*)\s*;\s*([A-Z]{2})\s*(?:#|$)")
VERSION_RE = re.compile(r"^#\s*Version:\s*([0-9.]+)\s*$", re.MULTILINE)

# Unicode scripts/blocks whose confusables belong to other charaudit
# categories (FULLWIDTH_HALF / PUNCT_VARIANT / CJK handling), kept out of
# HOMOGLYPH_UN on purpose to avoid double reporting.
EXCLUDED_BLOCKS = (
    (0x2E80, 0x9FFF),    # CJK radicals, kana, Bopomofo, CJK punctuation, ideographs
    (0xF900, 0xFAFF),    # CJK compatibility ideographs
    (0xFF00, 0xFF9F),    # fullwidth forms + halfwidth katakana
    (0x1B000, 0x1B2FF),  # kana/hangul supplements
    (0x20000, 0x3FFFF),  # CJK extensions B..+
)
ALLOWED_TYPES = {"MA", "ML"}  # mixed-script confusables = the attack vector


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def parse_confusables(raw_path: Path) -> tuple[dict[str, list[str]], dict]:
    raw_bytes = raw_path.read_bytes()
    raw_sha256 = sha256_bytes(raw_bytes)
    text = raw_bytes.decode("utf-8")
    version_match = VERSION_RE.search(text)
    version = version_match.group(1) if version_match else "unknown"

    counts = {
        "data_lines": 0,
        "skipped_parse_error": 0,
        "skipped_multi_codepoint_source": 0,
        "skipped_multi_codepoint_target": 0,
        "skipped_type_not_mixed_script": 0,
        "skipped_target_not_ascii_printable": 0,
        "skipped_source_ascii": 0,
        "skipped_source_in_excluded_block": 0,
        "kept_pairs": 0,
    }
    types_seen: dict[str, int] = {}
    pairs: dict[str, set[str]] = {}

    for line in text.splitlines():
        if not line or line.startswith("#") or line.startswith("@"):
            continue
        counts["data_lines"] += 1
        match = LINE_RE.match(line)
        if not match:
            counts["skipped_parse_error"] += 1
            continue
        src_field, tgt_field, entry_type = match.group(1), match.group(2), match.group(3)
        types_seen[entry_type] = types_seen.get(entry_type, 0) + 1
        src_cps = src_field.split()
        tgt_cps = tgt_field.split()
        if len(src_cps) != 1:
            counts["skipped_multi_codepoint_source"] += 1
            continue
        if len(tgt_cps) != 1:
            counts["skipped_multi_codepoint_target"] += 1
            continue
        if entry_type not in ALLOWED_TYPES:
            counts["skipped_type_not_mixed_script"] += 1
            continue
        tgt = int(tgt_cps[0], 16)
        if not (0x21 <= tgt <= 0x7E):
            counts["skipped_target_not_ascii_printable"] += 1
            continue
        src = int(src_cps[0], 16)
        if src < 0x80:
            # ASCII->ASCII confusables (1/l, I/l, 0/O ...) would flag ordinary
            # digits/letters in every text; they belong to a future INFO class.
            counts["skipped_source_ascii"] += 1
            continue
        if any(lo <= src <= hi for lo, hi in EXCLUDED_BLOCKS):
            counts["skipped_source_in_excluded_block"] += 1
            continue
        pairs.setdefault(f"{src:04X}", set()).add(f"{tgt:04X}")

    mapping = {src: sorted(targets) for src, targets in sorted(pairs.items())}
    counts["kept_pairs"] = sum(len(v) for v in mapping.values())
    counts["kept_sources"] = len(mapping)

    meta = {
        "source": "Unicode confusables.txt (UTS #39 security mechanisms data)",
        "version": version,
        "downloaded_url": "https://www.unicode.org/Public/security/latest/confusables.txt",
        "downloaded_date": "2026-10-07",
        "note_pinned_url": (
            "As of 2026-10-07 unicode.org pins /Public/security/15.1.0/ and /16.0.0/ "
            "only; 18.0.0 exists via /latest/. The raw file is committed at "
            "data/raw/confusables.txt and content-pinned by raw_sha256."
        ),
        "raw_sha256": raw_sha256,
        "types_seen": dict(sorted(types_seen.items())),
        "filter_rule": (
            "keep entries whose type is mixed-script (MA/ML) with a single-codepoint "
            "source and a single ASCII-printable target (U+0021-U+007E); skip ASCII "
            "sources (ASCII->ASCII lookalikes such as 1/l belong to a future INFO "
            "category) and sources in blocks reserved for other charaudit categories "
            "(CJK, kana, fullwidth, CJK extensions)"
        ),
        "excluded_blocks_hex": [f"{lo:04X}-{hi:04X}" for lo, hi in EXCLUDED_BLOCKS],
        "counts": counts,
        "license": "Unicode License v3 - Data Files and Software",
        "license_file": "licenses/unicode-data-files-license.txt",
        "generator": "scripts/build_tables.py",
    }
    meta["map_sha256"] = sha256_bytes(canonical_json(mapping))
    return mapping, meta


def load_cjk_groups(cjk_path: Path) -> tuple[dict[str, list[str]], dict]:
    doc = json.loads(cjk_path.read_text(encoding="utf-8"))
    groups = doc["groups"]
    guard = set(doc["frequency_guard_chars"])
    mates: dict[str, set[str]] = {}
    errors: list[str] = []
    group_count = 0
    for gi, group in enumerate(groups):
        label = f"group[{gi}]"
        chars = group.get("chars", [])
        kind = group.get("kind", "unspecified")
        if not 2 <= len(chars) <= 6:
            errors.append(f"{label}: size {len(chars)} outside 2..6")
            continue
        if len(set(chars)) != len(chars):
            errors.append(f"{label}: duplicate chars")
            continue
        for ch in chars:
            cp = ord(ch)
            if not (0x3400 <= cp <= 0x9FFF):
                errors.append(f"{label}: {ch!r} U+{cp:04X} outside CJK unified range")
            if ch in guard:
                errors.append(f"{label}: {ch!r} hits frequency guard list")
        for ch in chars:
            mates.setdefault(ch, set()).update(c for c in chars if c != ch)
        group_count += 1
        del kind
    if errors:
        print("CJK validation FAILED:", file=sys.stderr)
        for err in errors:
            print("  -", err, file=sys.stderr)
        raise SystemExit(1)

    mapping = {f"{ord(ch):04X}": sorted(mates[ch], key=ord) for ch in sorted(mates, key=ord)}
    meta = {
        "title": "CJK 形近字混淆集（自策展，hand-curated）",
        "date": doc["date"],
        "license": "MIT",
        "curation": doc["curation_note"],
        "kinds": doc["kinds"],
        "frequency_guard": doc["frequency_guard_note"],
        "frequency_guard_chars": doc["frequency_guard_chars"],
        "group_count": group_count,
        "char_count": len(mapping),
        "map_sha256": sha256_bytes(canonical_json(mapping)),
        "generator": "scripts/build_tables.py",
    }
    return mapping, meta


def write_json(path: Path, meta: dict, section_name: str, section: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {"_meta": meta, section_name: section}
    path.write_text(json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {path} ({path.stat().st_size} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/confusables.txt"))
    parser.add_argument("--cjk", type=Path, default=Path("data/cjk_confusables.json"))
    parser.add_argument("--out", type=Path, default=Path("src/charaudit/data"))
    args = parser.parse_args()

    mapping, meta = parse_confusables(args.raw)
    print(f"confusables: version={meta['version']} raw_sha256={meta['raw_sha256']}")
    for key, value in meta["counts"].items():
        print(f"  {key}: {value}")
    write_json(args.out / "confusables_un.json", meta, "map", mapping)

    cjk_map, cjk_meta = load_cjk_groups(args.cjk)
    print(f"cjk: groups={cjk_meta['group_count']} chars={cjk_meta['char_count']}")
    write_json(args.out / "cjk_confusables.json", cjk_meta, "mates", cjk_map)


if __name__ == "__main__":
    main()
