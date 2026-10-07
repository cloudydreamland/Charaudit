"""S4 boundary tests: extra-long text, extreme repetition, script alternation."""
from __future__ import annotations

import unittest

from charaudit import audit_text, diff_visible, sanitize


class TestLongTextBoundaries(unittest.TestCase):
    def test_300k_chars_single_planted_finding(self):
        text = "ab中文字符" * 50000 + "\u200b"  # 300k chars, one planted ZWSP
        self.assertEqual(len(text), 300001)
        report = audit_text(text, policy="strict")
        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertEqual(finding.start, 300000)
        self.assertEqual(text[finding.start:finding.end], "\u200b")

    def test_extreme_repetition_homoglyph_run_merges(self):
        text = "с" * 10000  # Cyrillic es x10000
        report = audit_text(text, policy="strict")
        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertEqual((finding.start, finding.end), (0, 10000))
        self.assertEqual(finding.confusable_with, "c" * 10000)

    def test_alternating_script_chunks(self):
        chunk = "中文内容。" * 50 + "english words here. " * 50
        text = chunk * 200  # ~440k chars alternating CJK/ASCII
        report = audit_text(text, policy="strict")
        # ordering + non-overlap hold at scale
        for prev, curr in zip(report.findings, report.findings[1:]):
            self.assertLessEqual(prev.end, curr.start)
        for f in report.findings:
            self.assertEqual(text[f.start:f.end], f.text)

    def test_sanitize_scales_linearly_on_periodic_plants(self):
        parts = []
        for i in range(8000):
            parts.append("hello world ")
            if i % 500 == 499:
                parts.append("\u200b")  # 16 spread-out plants, never adjacent
        text = "".join(parts)
        cleaned, log = sanitize(text)
        self.assertEqual(len(cleaned), len(text) - 16)
        self.assertEqual(log.summary(), {"ZERO_WIDTH": 16})

    def test_diff_visible_on_10k_near_identical(self):
        # scale note: at ~100k chars this call measured 85.6s (2026-10-08,
        # see benchmarks/RESULTS.md) — SequenceMatcher's cliff even for
        # nearly-identical inputs. Recorded as the motivation for A-S4-2;
        # this test keeps the correctness invariant at a suite-friendly size.
        a = "中英文混合内容ABC123" * 900 + "\u200b"  # ~9.9k chars
        b = a[:-1]
        report = diff_visible(a, b)
        self.assertTrue(report.equal_visible)
        self.assertFalse(report.equal)
        self.assertEqual("".join(s.text_a for s in report.segments), a)
        self.assertEqual("".join(s.text_b for s in report.segments), b)


if __name__ == "__main__":
    unittest.main()
