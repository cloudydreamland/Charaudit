"""Character tables: invisible-character ranges + homoglyph lookup tables.

Range tables (FORBIDDEN classes) are hand-maintained and versioned together
with the Unicode database that ships with the running interpreter. Homoglyph
tables are built by ``scripts/build_tables.py`` from auditable sources and
shipped as package data with per-file SHA-256 fingerprints:

- ``HOMOGLYPH_UN``  Unicode confusables.txt (UTS #39), filtered to
  mixed-script single-codepoint sources with a single ASCII-printable target,
  excluding blocks reserved for other charaudit categories.
- ``HOMOGLYPH_CJK`` hand-curated Chinese near-homograph groups (形近字),
  MIT-licensed, see ``data/cjk_confusables.json`` for curation rules.

``TABLE_FINGERPRINTS`` carries the SHA-256 of every shipped table so audit
evidence stays reproducible; ``TABLE_VERSION`` is embedded into every Report.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

UNICODE_VERSION = unicodedata.unidata_version
CONFUSABLES_VERSION = "unknown"  # parsed from the shipped table's _meta
CJK_VERSION = "2026-10-07"  # curation date of the shipped CJK table
TABLE_VERSION = f"2026.10-unicode{UNICODE_VERSION}+confusables{CONFUSABLES_VERSION}"

ZERO_WIDTH = (
    (0x200B, 0x200D),  # ZWSP, ZWNJ, ZWJ
    (0x2060, 0x2064),  # WORD JOINER, invisible ops
    (0xFEFF, 0xFEFF),  # ZERO WIDTH NO-BREAK SPACE (BOM)
)
BIDI = (
    (0x202A, 0x202E),  # LRE RLE PDF LRO RLO
    (0x2066, 0x2069),  # LRI RLI FSI PDI
)
TAG_BLOCK = ((0xE0000, 0xE007F),)
SURROGATE_ORPHAN = ((0xD800, 0xDFFF),)
# C0 controls except tab/newline/carriage-return, DEL, C1 controls.
CONTROL = ((0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F), (0x7F, 0x7F), (0x80, 0x9F))
# Format characters beyond the invisible five (DESIGN §2: "SOFT_HYPHEN 等
# 其他 Cf"): soft hyphen, directional marks, deprecated format chars.
SOFT_HYPHEN = (
    (0x00AD, 0x00AD),  # SOFT HYPHEN
    (0x061C, 0x061C),  # ARABIC LETTER MARK
    (0x180E, 0x180E),  # MONGOLIAN VOWEL SEPARATOR (Cf since Unicode 6.3)
    (0x200E, 0x200F),  # LRM, RLM
    (0x206A, 0x206F),  # deprecated format characters
)
# Compatibility forms: fullwidth ASCII alphanumerics and halfwidth katakana
# (NFKC-normalizable; DESIGN §5: runtime ranges, no data table). Fullwidth
# PUNCTUATION is deliberately excluded here — it belongs to the contextual
# PUNCT_VARIANT class.
FULLWIDTH_HALF = (
    (0xFF10, 0xFF19),  # fullwidth digits ０-９, NFKC -> ASCII digits
    (0xFF21, 0xFF3A),  # fullwidth uppercase Ａ-Ｚ, NFKC -> ASCII
    (0xFF41, 0xFF5A),  # fullwidth lowercase ａ-ｚ, NFKC -> ASCII
    (0xFF61, 0xFF9F),  # halfwidth katakana and forms, NFKC -> fullwidth kana
)

_CATEGORIES = (
    ("ZERO_WIDTH", ZERO_WIDTH),
    ("BIDI", BIDI),
    ("TAG_BLOCK", TAG_BLOCK),
    ("SURROGATE_ORPHAN", SURROGATE_ORPHAN),
    ("CONTROL", CONTROL),
    ("SOFT_HYPHEN", SOFT_HYPHEN),
    ("FULLWIDTH_HALF", FULLWIDTH_HALF),
)

# Categories that are invisible or structurally hostile to rendering order —
# what diff_visible treats as "hidden". Homoglyphs and fullwidth forms are
# VISIBLE characters, so they must not count as hidden.
INVISIBLE_CATEGORIES = frozenset(
    {"ZERO_WIDTH", "BIDI", "TAG_BLOCK", "SURROGATE_ORPHAN", "CONTROL", "SOFT_HYPHEN"}
)

_NOTES = {
    "ZERO_WIDTH": (
        "Zero-width characters are invisible in rendered text but read by LLMs; "
        "U+200C/200D are orthographically legitimate in Arabic and Indic scripts, "
        "so review context before removing."
    ),
    "BIDI": (
        "Bidirectional controls can visually reorder source text "
        "(Trojan Source technique); legitimate only in specialized editing tools."
    ),
    "TAG_BLOCK": (
        "Unicode tag characters have no legitimate plain-text use and are abused "
        "to hide prompt-injection payloads (AWS Security Blog, 2025-09-30)."
    ),
    "SURROGATE_ORPHAN": (
        "Lone surrogate code point; breaks UTF-8/UTF-16 encoding and can "
        "recombine into invisible tag characters at byte boundaries."
    ),
    "CONTROL": (
        "Control character other than tab/newline/carriage-return; used for "
        "terminal injection and log forgery."
    ),
    "HOMOGLYPH_UN": (
        "Mixed-script homoglyph: looks like an ASCII character but belongs to "
        "another script (Unicode confusables.txt); classic spoofing, phishing, "
        "and typosquatting vector. Fully legitimate in text actually written in "
        "that script (e.g. Cyrillic in Russian) — judge by context."
    ),
    "HOMOGLYPH_CJK": (
        "Chinese near-homograph (形近字): easily mistaken for its listed twins. "
        "These characters are common in perfectly ordinary Chinese text, so a "
        "hit is a review hint (typos, evasive keyword substitution, name "
        "collisions), not an error — judge by context."
    ),
    "SOFT_HYPHEN": (
        "Format character beyond the invisible five: soft hyphen changes "
        "line-breaking, LRM/RLM and deprecated format characters steer "
        "direction resolution invisibly. Classic exact-match filter evasion — "
        "legitimate in some typesetting workflows, review context."
    ),
    "FULLWIDTH_HALF": (
        "Compatibility form: fullwidth ASCII variant or halfwidth katakana, "
        "NFKC-normalizes to its ASCII/kana counterpart. Normalization hint "
        "for Chinese corpora and exact-match pipelines, not an error."
    ),
    "PUNCT_VARIANT": (
        "Punctuation in the minority script of this string (中文/西文标点混排): "
        "a normalization/style hint only, never an error. Decided per string "
        "by dominant-script context, not by classify()."
    ),
}

_DATA_DIR = Path(__file__).parent / "data"


def _load_packaged(filename: str) -> tuple[dict, dict]:
    raw = (_DATA_DIR / filename).read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    return doc["_meta"], doc


_UN_META, _UN_DOC = _load_packaged("confusables_un.json")
_CJK_META, _CJK_DOC = _load_packaged("cjk_confusables.json")
CONFUSABLES_VERSION = _UN_META["version"]
TABLE_VERSION = f"2026.10-unicode{UNICODE_VERSION}+confusables{CONFUSABLES_VERSION}"

HOMOGLYPH_UN: dict[str, str] = {
    chr(int(src_hex, 16)): "".join(chr(int(t_hex, 16)) for t_hex in targets)
    for src_hex, targets in _UN_DOC["map"].items()
}
HOMOGLYPH_CJK: dict[str, str] = {
    chr(int(cp_hex, 16)): "/".join(mates)
    for cp_hex, mates in _CJK_DOC["mates"].items()
}

TABLE_FINGERPRINTS = {
    "confusables_un.json": hashlib.sha256(
        (_DATA_DIR / "confusables_un.json").read_bytes()
    ).hexdigest(),
    "cjk_confusables.json": hashlib.sha256(
        (_DATA_DIR / "cjk_confusables.json").read_bytes()
    ).hexdigest(),
}

_HOMOGLYPH_CATEGORY = {"HOMOGLYPH_UN": HOMOGLYPH_UN, "HOMOGLYPH_CJK": HOMOGLYPH_CJK}

# PUNCT_VARIANT is the only context-dependent category: classify() stays
# context-free and returns None for these characters. The scanner decides
# per string which script is dominant and flags only the intruding variant,
# so ordinary single-script text never produces punctuation noise.
CJK_CONTEXT_RANGES = (
    (0x2E80, 0x9FFF),   # CJK radicals/kana/ideographs
    (0xF900, 0xFAFF),   # CJK compatibility ideographs
    (0xAC00, 0xD7AF),   # Hangul syllables
)
# ASCII punctuation flagged inside CJK-dominant text.
ASCII_PUNCT_IN_CJK = ",;:?!()\"'"
# Fullwidth punctuation flagged inside non-CJK text.
FULLWIDTH_PUNCT_IN_ASCII = "，；：？！（）"
# Dominant-script counterpart, carried as Finding.confusable_with evidence.
PUNCT_TWIN = {
    ",": "，", ";": "；", ":": "：", "?": "？", "!": "！",
    "(": "（", ")": "）", '"': "“”", "'": "‘’",
    "，": ",", "；": ";", "：": ":", "？": "?", "！": "!",
    "（": "(", "）": ")",
}


def classify(ch: str) -> str | None:
    """Return the audit category name for *ch*, or None if benign.

    Range classes (invisible characters) are checked first; homoglyph tables
    only contain visible confusable characters, so the two can never overlap.
    """
    cp = ord(ch)
    for name, ranges in _CATEGORIES:
        for lo, hi in ranges:
            if lo <= cp <= hi:
                return name
    if cp >= 0x80:  # packaged tables hold no ASCII sources (see filter_rule)
        for name, table in _HOMOGLYPH_CATEGORY.items():
            if ch in table:
                return name
    return None


def is_invisible(ch: str) -> bool:
    """True for invisible/structurally hostile characters (diff "hidden" class).

    Homoglyphs are visible characters that look like others — not invisible.
    """
    return classify(ch) in INVISIBLE_CATEGORIES


def homoglyph_targets(ch: str) -> str:
    """For a homoglyph character, the characters it can be mistaken for."""
    for table in _HOMOGLYPH_CATEGORY.values():
        if ch in table:
            return table[ch]
    return ""


def note_for(category: str) -> str:
    return _NOTES.get(category, "")
