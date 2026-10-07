"""Single-pass scanner for invisible characters and homoglyph confusables."""
from __future__ import annotations

import unicodedata
from typing import Iterable, Iterator, Mapping

from ._tables import (
    ASCII_PUNCT_IN_CJK,
    CJK_CONTEXT_RANGES,
    FULLWIDTH_PUNCT_IN_ASCII,
    PUNCT_TWIN,
    TABLE_VERSION,
    classify,
    homoglyph_targets,
    note_for,
)
from .model import Finding, Report
from .policy import POLICY_VERSION, resolve_policy


def _punct_variant_findings(text: str, risk: str, suggestion: str) -> list[Finding]:
    """PUNCT_VARIANT: flag punctuation of the minority script of *text*.

    The only context-dependent category — classify() stays context-free and
    returns None for these characters, so single-script text never produces
    punctuation noise and only the intruding variant is reported.
    """
    cjk_context = any(
        lo <= ord(ch) <= hi for ch in text for lo, hi in CJK_CONTEXT_RANGES
    )
    intruders = ASCII_PUNCT_IN_CJK if cjk_context else FULLWIDTH_PUNCT_IN_ASCII
    findings: list[Finding] = []
    for i, ch in enumerate(text):
        if ch not in intruders:
            continue
        findings.append(
            Finding(
                category="PUNCT_VARIANT",
                risk=risk,
                start=i,
                end=i + 1,
                text=ch,
                codepoint=f"U+{ord(ch):04X}",
                unicode_name=unicodedata.name(ch, f"<unnamed U+{ord(ch):04X}>"),
                note=note_for("PUNCT_VARIANT"),
                suggestion=suggestion,
                confusable_with=PUNCT_TWIN.get(ch, ""),
            )
        )
    return findings


def audit_text(
    text: str,
    *,
    policy: str | Mapping[str, tuple[str, str]] = "neutral",
) -> Report:
    """Audit *text* and return a Report with exact-offset findings.

    Adjacent characters of the same category are merged into one Finding.
    Findings are ordered by start offset and never overlap.
    """
    if not isinstance(text, str):
        raise TypeError(
            f"charaudit audits str only, got {type(text).__name__}; decode bytes "
            "yourself and declare the source encoding (see DESIGN.md section 4)"
        )
    resolved = resolve_policy(policy)
    findings: list[Finding] = []
    n = len(text)
    i = 0
    while i < n:
        category = classify(text[i])
        if category is None or category not in resolved:
            i += 1
            continue
        j = i + 1
        while j < n and classify(text[j]) == category:
            j += 1
        segment = text[i:j]
        risk, suggestion = resolved[category]
        if category == "HOMOGLYPH_UN":
            # deception rendering: what the run reads as (e.g. "сс" -> "cc")
            confusable_with = "".join(homoglyph_targets(ch) for ch in segment)
        elif category == "HOMOGLYPH_CJK":
            confusable_with = ";".join(
                dict.fromkeys(
                    target for ch in segment if (target := homoglyph_targets(ch))
                )
            )
        else:
            confusable_with = ""
        findings.append(
            Finding(
                category=category,
                risk=risk,
                start=i,
                end=j,
                text=segment,
                codepoint=f"U+{ord(segment[0]):04X}",
                unicode_name=unicodedata.name(
                    segment[0], f"<unnamed U+{ord(segment[0]):04X}>"
                ),
                note=note_for(category),
                suggestion=suggestion,
                confusable_with=confusable_with,
            )
        )
        i = j
    if "PUNCT_VARIANT" in resolved:
        risk, suggestion = resolved["PUNCT_VARIANT"]
        findings.extend(_punct_variant_findings(text, risk, suggestion))
        findings.sort(key=lambda f: f.start)
    policy_name = policy if isinstance(policy, str) else "custom"
    return Report(
        source=text,
        findings=tuple(findings),
        policy=policy_name,
        policy_version=POLICY_VERSION,
        table_version=TABLE_VERSION,
    )


def audit_prompt(text: str, **kwargs) -> Report:
    """Audit LLM prompt input with the strict policy."""
    return audit_text(text, policy="strict", **kwargs)


def audit_corpus(
    texts: Iterable[str],
    *,
    policy: str | Mapping[str, tuple[str, str]] = "neutral",
) -> Iterator[Report]:
    """Stream-audit many texts; yields one Report per input, constant memory.

    Returns a lazy iterator, but the policy is validated eagerly — a bad
    preset name fails at call time rather than mid-stream.
    """
    resolve_policy(policy)  # eager validation
    return _iter_corpus(texts, policy)


def _iter_corpus(
    texts: Iterable[str],
    policy: str | Mapping[str, tuple[str, str]],
) -> Iterator[Report]:
    for text in texts:
        yield audit_text(text, policy=policy)
