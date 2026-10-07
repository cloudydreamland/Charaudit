"""Data models. Findings carry exact source offsets (offset invariant)."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Finding:
    """One contiguous run of same-category characters in the source text.

    Invariant (fuzz-guarded): ``finding.text == source[start:end]``.
    """

    category: str
    risk: str
    start: int
    end: int
    text: str
    codepoint: str
    unicode_name: str
    note: str
    suggestion: str
    # for HOMOGLYPH_* findings: the character(s) this run can be mistaken for
    # (e.g. "c" for Cyrillic с, "已/巳" for 己); "" for all other categories.
    confusable_with: str = ""


@dataclass(frozen=True)
class Report:
    """Audit result for one source string."""

    source: str
    findings: tuple[Finding, ...] = field(default=())
    policy: str = "neutral"
    policy_version: str = "1"
    table_version: str = "unknown"

    def stats(self) -> dict[str, int]:
        """Finding counts per category."""
        return dict(Counter(f.category for f in self.findings))
