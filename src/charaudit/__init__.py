"""The Ghosts in the Ink (charaudit).

Chinese-first invisible-character auditing for prompts, corpora, and text
pipelines. Deterministic and character-level: it finds invisible and
confusable Unicode, it does not judge semantics.
"""
from .diff import DiffReport, DiffSegment
from .diff import diff_visible as _diff_visible
from .sanitize import Change, ChangeLog
from .sanitize import sanitize as _sanitize
from ._tables import (
    CONFUSABLES_VERSION,
    TABLE_FINGERPRINTS,
    TABLE_VERSION,
    UNICODE_VERSION,
)
from .model import Finding, Report
from .policy import (
    ALL_CATEGORIES,
    FORBIDDEN_CATEGORIES,
    INFO_CATEGORIES,
    SUSPICIOUS_CATEGORIES,
    resolve_policy,
)
from .scanner import audit_corpus, audit_prompt, audit_text

__all__ = [
    "audit_text",
    "audit_prompt",
    "audit_corpus",
    "diff_visible",
    "sanitize",
    "Finding",
    "Report",
    "Change",
    "ChangeLog",
    "DiffReport",
    "DiffSegment",
    "resolve_policy",
    "FORBIDDEN_CATEGORIES",
    "SUSPICIOUS_CATEGORIES",
    "INFO_CATEGORIES",
    "ALL_CATEGORIES",
    "UNICODE_VERSION",
    "CONFUSABLES_VERSION",
    "TABLE_VERSION",
    "TABLE_FINGERPRINTS",
    "__version__",
]
__version__ = "0.1.0a1"


def sanitize(text: str, *, policy: str = "strict"):
    """Delete-only removal of flagged characters; returns (cleaned, ChangeLog)."""
    return _sanitize(text, policy=policy)


def diff_visible(a: str, b: str):
    """Explain why two look-alike strings are not equal."""
    return _diff_visible(a, b)
