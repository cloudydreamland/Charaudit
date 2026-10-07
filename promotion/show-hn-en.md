# Show HN draft — status: DRAFT, waiting for posting credentials

> Target: news.ycombinator.com "Show HN". Rules check before posting: Show HN =
> something people can try (repo is live ✓); no title case; no marketing speak;
> author should stick around for comments. One post at a time; link goes into
> PIPELINE_STATE.md after posting. If PyPI is live by then, mention it in the
> first comment instead of editing the title.

---

**Title**: Show HN: Charaudit – find invisible characters and homoglyphs in text, pure stdlib

**Body**:

Hi HN — I built a small tool for a problem that keeps biting people who process
text from untrusted sources: characters you cannot see, and characters that look
like other characters.

Three examples from real write-ups:

- Zero-width characters (U+200B) can smuggle instructions into LLM prompts; the
  model reads them token-by-token, humans see nothing (promptfoo, Apr 2025).
- Unicode tag characters (U+E0000–E007F) hide payloads, and lone UTF-16
  surrogates can recombine into new invisible characters at byte boundaries
  (AWS Security Blog, Sep 2025).
- "sеcure-paypal.com" contains a Cyrillic е (U+0435). Identical glyphs,
  different code points — comparisons silently fail.

charaudit scans text and reports these with exact source offsets. It also
ships:

- `diff_visible` — explains why two look-alike strings are not equal, per
  character (linear on near-identical input: a 100k-char pair went from 85.6s
  to 0.168s after I measured and fixed a difflib cliff; numbers in the repo);
- `sanitize` — delete-only removal whose change log points back into the
  original text, with a UTF-16 recombination guard;
- a curated table of ~250 Chinese near-homograph groups (己/已/巳, 末/未 …),
  because homoglyph confusion is not Latin-only;
- streaming audit for corpora.

Design stance: deterministic and character-level only. It does not judge
semantics, and "no findings" means "none in these categories under this
policy/table version" — not "this text is safe". Findings carry evidence
(code point, offset, what the character can be mistaken for), and every data
table is content-pinned with SHA-256 fingerprints asserted by tests.

Pure standard library, no required dependencies, 85 tests, CI on
ubuntu/windows × Python 3.10–3.13. It is an **alpha** (0.1.0a1) — not on PyPI
yet.

https://github.com/cloudydreamland/Charaudit

I would especially like feedback on the API surface
(`audit_text / audit_prompt / audit_corpus / diff_visible / sanitize`) and on
which false-positive trade-offs feel acceptable (e.g. the Chinese homograph
table deliberately flags common characters like 请 as review hints).
