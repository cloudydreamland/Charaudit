# Reddit r/Python draft — status: DRAFT, waiting for posting credentials

> Target: r/Python as a text post ("I wrote a library..."). Subreddit rules to
> re-check before posting (self-promotion limits). One post at a time; record
> the link in PIPELINE_STATE.md after posting. If PyPI is live by then, swap
> the install section to `pip install charaudit`.

---

**Title**: I wrote charaudit — find invisible characters and look-alike homoglyphs in prompts/corpora (pure stdlib, zero dependencies, alpha)

**Body**:

Two strings look identical. One `==` check passes, the other fails. Or worse:
an LLM reads a prompt that contains hidden instructions no human can see.

This is not hypothetical:

- promptfoo demonstrated (Apr 2025) zero-width character (U+200B) injection into
  prompts — invisible in rendering, read token-by-token by the model;
- AWS Security Blog (Sep 2025) documented payloads hidden in Unicode tag
  characters (U+E0000–E007F), including recombining lone surrogates at UTF-16
  byte boundaries;
- `sеcure-paypal.com` — that е is Cyrillic U+0435, identical in most fonts, and
  string comparison never matches.

The existing tooling has a gap: `confusable_homoglyphs` (~1.37M downloads/month)
has been archived since Jan 2024 and only covers homoglyphs, not invisible
characters; `llm-guard` is archived too.

So I built **charaudit**: deterministic, character-level auditing for prompts,
corpora, and text pipelines. Chinese-first (ships a curated Chinese
near-homograph table), pure stdlib, zero required dependencies.

```python
from charaudit import audit_prompt
report = audit_prompt('Admin login: sеcure-paypal.com')
for f in report.findings:
    print(f.category, f.start, f.codepoint, f.confusable_with, f.suggestion)
```

```text
HOMOGLYPH_UN 14 U+0435 e REVIEW
```

It also detects zero-width characters, bidi controls (Trojan Source), Unicode
tag blocks, lone surrogates, C0/C1 controls, soft hyphens, fullwidth/halfwidth
forms, mixed-script punctuation, and ships `diff_visible` ("why are these two
strings not equal?", with a per-character Chinese explanation), `sanitize`
(delete-only removal whose offsets point back into the original text), and
`audit_corpus` (streaming).

**Honest boundaries** (also in the README): character-level detection only — it
does not judge semantics and is not an "injection firewall"; "no findings" means
"none in these categories under this policy/table version", not "this text is
safe". It is an **alpha** (0.1.0a1), not yet on PyPI. Chinese common characters
in the curated near-homograph table (己/已/巳 …) produce REVIEW hints in ordinary
prose — that trade-off is documented, not hidden.

Everything is auditable: the Unicode confusables source file is committed with
its SHA-256, the curated table's curation rules are public, shipped tables carry
fingerprints asserted by tests, and benchmarks are reproducible (85.6s → 0.168s
for a 100k near-identical diff is documented before/after).

Repo (design docs, research evidence chain, reproducible benchmarks):
https://github.com/cloudydreamland/Charaudit

Feedback I would value most: API shape (`audit_text / audit_prompt /
audit_corpus / diff_visible / sanitize`), default policy presets, and which
direction the Chinese homograph table should be curated toward (typo QC /
phishing resistance / keyword-evasion detection).
