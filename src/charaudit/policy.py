"""Policies map character categories to (risk, suggestion) pairs.

Presets:
- strict   (audit_prompt): all FORBIDDEN classes removed; homoglyphs and
  soft-hyphen-class format chars flagged SUSPICIOUS; INFO classes reported.
- balanced (audit_corpus): CONTROL downgraded to SUSPICIOUS/REVIEW.
- neutral  (audit_text):  report only, no removal advice.

Policy version history:
- "3": added SOFT_HYPHEN (SUSPICIOUS) and the INFO classes FULLWIDTH_HALF /
  PUNCT_VARIANT.
- "2": added HOMOGLYPH_UN / HOMOGLYPH_CJK (SUSPICIOUS in every preset).
- "1": the five FORBIDDEN classes only.
"""
from __future__ import annotations

from typing import Mapping

POLICY_VERSION = "3"

RISK_FORBIDDEN = "FORBIDDEN"
RISK_SUSPICIOUS = "SUSPICIOUS"
RISK_INFO = "INFO"

S_REMOVE = "REMOVE"
S_REVIEW = "REVIEW"

FORBIDDEN_CATEGORIES = (
    "ZERO_WIDTH",
    "BIDI",
    "TAG_BLOCK",
    "SURROGATE_ORPHAN",
    "CONTROL",
)
SUSPICIOUS_CATEGORIES = (
    "HOMOGLYPH_UN",
    "HOMOGLYPH_CJK",
    "SOFT_HYPHEN",
)
INFO_CATEGORIES = (
    "FULLWIDTH_HALF",
    "PUNCT_VARIANT",
)
ALL_CATEGORIES = FORBIDDEN_CATEGORIES + SUSPICIOUS_CATEGORIES + INFO_CATEGORIES

_STRICT_RULE = (RISK_FORBIDDEN, S_REMOVE)
_REVIEW_RULE = (RISK_SUSPICIOUS, S_REVIEW)
_INFO_RULE = (RISK_INFO, S_REVIEW)

_SUSPICIOUS_RULES = {c: _REVIEW_RULE for c in SUSPICIOUS_CATEGORIES}
_INFO_RULES = {c: _INFO_RULE for c in INFO_CATEGORIES}

STRICT: dict[str, tuple[str, str]] = {
    **{c: _STRICT_RULE for c in FORBIDDEN_CATEGORIES},
    **_SUSPICIOUS_RULES,
    **_INFO_RULES,
}
BALANCED: dict[str, tuple[str, str]] = {
    **{c: _STRICT_RULE for c in FORBIDDEN_CATEGORIES if c != "CONTROL"},
    "CONTROL": _REVIEW_RULE,
    **_SUSPICIOUS_RULES,
    **_INFO_RULES,
}
NEUTRAL: dict[str, tuple[str, str]] = {
    **{c: _REVIEW_RULE for c in FORBIDDEN_CATEGORIES + SUSPICIOUS_CATEGORIES},
    **_INFO_RULES,
}

PRESETS: dict[str, Mapping[str, tuple[str, str]]] = {
    "strict": STRICT,
    "balanced": BALANCED,
    "neutral": NEUTRAL,
}


def resolve_policy(policy: str | Mapping[str, tuple[str, str]]) -> dict[str, tuple[str, str]]:
    """Accept a preset name or a custom category->(risk, suggestion) mapping."""
    if isinstance(policy, str):
        try:
            return dict(PRESETS[policy])
        except KeyError:
            raise ValueError(
                f"unknown policy {policy!r}; valid presets: {sorted(PRESETS)}"
            ) from None
    resolved = dict(policy)
    for category, rule in resolved.items():
        if category not in ALL_CATEGORIES:
            raise ValueError(f"unknown category {category!r}")
        if (
            not isinstance(rule, tuple)
            or len(rule) != 2
            or rule[0] not in (RISK_FORBIDDEN, RISK_SUSPICIOUS, RISK_INFO)
            or rule[1] not in (S_REMOVE, S_REVIEW)
        ):
            raise ValueError(f"invalid rule {rule!r} for category {category!r}")
    return resolved
