"""sanitize: delete-only removal of flagged characters, with evidence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .policy import S_REMOVE, resolve_policy
from .scanner import audit_text

MAX_ROUNDS = 8


@dataclass(frozen=True)
class Change:
    """One removal. Offsets refer to the ORIGINAL text (offset invariant):

    ``change.removed == original[change.start:change.end]``
    """

    start: int
    end: int
    removed: str
    category: str
    reason: str


@dataclass(frozen=True)
class ChangeLog:
    changes: tuple[Change, ...]
    source_length: int
    rounds: int

    def summary(self) -> dict[str, int]:
        """Change counts per category."""
        counts: dict[str, int] = {}
        for change in self.changes:
            counts[change.category] = counts.get(change.category, 0) + 1
        return counts


def sanitize(
    text: str,
    *,
    policy: str | Mapping[str, tuple[str, str]] = "strict",
) -> tuple[str, ChangeLog]:
    """Remove characters whose policy suggestion is REMOVE; delete-only.

    Returns ``(cleaned_text, ChangeLog)``. Change offsets always refer to the
    original text. Policies without REMOVE rules (e.g. ``neutral``) are a
    no-op. For policies that flag SURROGATE_ORPHAN, the cleaned text is
    verified UTF-16 round-trip stable (surrogatepass), guarding the
    byte-boundary recombination described in DESIGN.md section 4.
    """
    if not isinstance(text, str):
        raise TypeError(
            f"charaudit sanitize accepts str only, got {type(text).__name__}"
        )
    resolved = resolve_policy(policy)
    policy_name = policy if isinstance(policy, str) else "custom"
    index_map = list(range(len(text)))  # current index -> original index
    changes: list[Change] = []
    current = text
    rounds = 0
    while True:
        rounds += 1
        if rounds > MAX_ROUNDS:
            raise RuntimeError(
                f"sanitize did not reach a fixpoint within {MAX_ROUNDS} rounds"
            )
        report = audit_text(current, policy=resolved)
        removals = [f for f in report.findings if f.suggestion == S_REMOVE]
        if not removals:
            break
        parts: list[str] = []
        new_map: list[int] = []
        pos = 0
        for finding in removals:
            parts.append(current[pos:finding.start])
            new_map.extend(index_map[pos:finding.start])
            changes.append(
                Change(
                    start=index_map[finding.start],
                    end=index_map[finding.end - 1] + 1,
                    removed=finding.text,
                    category=finding.category,
                    reason=(
                        f"{finding.category} ({finding.codepoint}) is {finding.risk} "
                        f"under policy '{policy_name}'"
                    ),
                )
            )
            pos = finding.end
        parts.append(current[pos:])
        new_map.extend(index_map[pos:])
        current = "".join(parts)
        index_map = new_map
    if "SURROGATE_ORPHAN" in resolved:
        roundtrip = current.encode("utf-16", "surrogatepass").decode(
            "utf-16", "surrogatepass"
        )
        if roundtrip != current:
            raise RuntimeError("cleaned text is not UTF-16 round-trip stable")
    return current, ChangeLog(tuple(changes), len(text), rounds)
