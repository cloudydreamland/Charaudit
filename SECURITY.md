# Security Policy — charaudit

## Supported versions

| Version | Supported |
|---|---|
| 0.1.0a1 (pre-release) | yes — best effort, fixes land in the next alpha |

Pre-release versions are never presented as stable; pin exactly what you audit with.

## What this project is (and is not)

`charaudit` is an **offline, deterministic text-auditing library**. It:

- performs no network I/O at runtime,
- executes no input text (input is data, never code),
- ships no executable payloads — only Python source and JSON data tables.

"Security" here is about **audit honesty**, not sandboxing:

1. every finding satisfies the offset invariant `finding.text == source[start:end]`
   (fuzz-guarded);
2. `sanitize` is delete-only, and its ChangeLog always points back into the original
   text;
3. shipped data tables are content-pinned: `charaudit.TABLE_FINGERPRINTS` carries the
   SHA-256 of every packaged table, asserted against the files by tests, and each
   table's `_meta` records source URL, version, raw-file SHA-256, and the exact
   filter/curation rule.

## Reporting a vulnerability

- Preferred: open a **private security advisory** via GitHub (Security → Advisories)
  on the repository.
- If GitHub is unavailable, open a normal issue titled `security: …` with details you
  are comfortable publishing publicly — given the offline nature of this library,
  there is little that requires coordinated disclosure.
- Please include: version, a minimal reproducer, and the observed vs. expected
  evidence (findings, offsets, table fingerprints).

In scope: offset-invariant violations, sanitize leaving flagged characters behind
under a policy whose rule is REMOVE, data-table provenance mismatches (file bytes vs.
`TABLE_FINGERPRINTS` / `_meta`), classification errors that materially change audit
verdicts.

Out of scope: semantic detection gaps (the library is character-level by design;
"no findings" means "none in these categories under this policy/table version"), the
documented false-positive surface of `HOMOGLYPH_CJK` and `PUNCT_VARIANT`, and
performance on non-recommended workloads (see `benchmarks/RESULTS.md`).
