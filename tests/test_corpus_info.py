"""Tests for audit_corpus and the SOFT_HYPHEN / FULLWIDTH_HALF / PUNCT_VARIANT classes."""
from __future__ import annotations
import unittest

from collections.abc import Iterator

from charaudit import (
    INFO_CATEGORIES,
    audit_corpus,
    audit_prompt,
    audit_text,
    resolve_policy,
    sanitize,
)
from charaudit._tables import PUNCT_TWIN, classify


class TestSoftHyphenClass(unittest.TestCase):
    def test_soft_hyphen_flagged_all_presets(self):
        for preset in ("strict", "balanced", "neutral"):
            report = audit_text("inter\u00ADnational", policy=preset)
            self.assertEqual([f.category for f in report.findings], ["SOFT_HYPHEN"])
            self.assertEqual(report.findings[0].risk, "SUSPICIOUS", preset)
            self.assertEqual(report.findings[0].suggestion, "REVIEW", preset)

    def test_direction_marks_and_deprecated_format_chars(self):
        report = audit_text("a\u200eb\u061Cc\u206ad")
        self.assertEqual(
            [f.category for f in report.findings], ["SOFT_HYPHEN"] * 3
        )
        self.assertEqual([f.codepoint for f in report.findings], ["U+200E", "U+061C", "U+206A"])

    def test_soft_hyphen_is_invisible_for_diff(self):
        from charaudit._tables import is_invisible

        self.assertTrue(is_invisible("\u00AD"))

    def test_strict_sanitize_keeps_custom_policy_removes(self):
        cleaned, log = sanitize("in\u00ADput")  # SUSPICIOUS under strict: kept
        self.assertEqual(cleaned, "in\u00ADput")
        self.assertEqual(log.changes, ())
        cleaned, log = sanitize("in\u00ADput", policy={"SOFT_HYPHEN": ("SUSPICIOUS", "REMOVE")})
        self.assertEqual(cleaned, "input")
        self.assertEqual(log.changes[0].category, "SOFT_HYPHEN")


class TestFullwidthHalfClass(unittest.TestCase):
    def test_fullwidth_ascii_and_halfwidth_katakana_flagged_info(self):
        report = audit_text("Ａｐｐｌｅ１２３")
        self.assertEqual([f.category for f in report.findings], ["FULLWIDTH_HALF"])
        self.assertEqual(report.findings[0].risk, "INFO")
        self.assertEqual(report.findings[0].codepoint, "U+FF21")
        report = audit_text("ｱｲｳ")
        self.assertEqual([f.category for f in report.findings], ["FULLWIDTH_HALF"])
        self.assertEqual(report.findings[0].codepoint, "U+FF71")

    def test_plain_ascii_and_fullwidth_katakana_stay_clean(self):
        self.assertEqual(audit_text("Apple 123").findings, ())
        self.assertEqual(audit_text("アップル").findings, ())

    def test_note_mentions_nfkc(self):
        report = audit_text("ＡＢＣ")
        self.assertIn("NFKC", report.findings[0].note)


class TestPunctVariantClass(unittest.TestCase):
    def test_ascii_punct_inside_cjk_text_flagged(self):
        source = "他说\"你好\", 然后走了"
        report = audit_text(source)
        self.assertEqual(
            [(f.category, f.risk) for f in report.findings],
            [("PUNCT_VARIANT", "INFO")] * 3,
        )
        self.assertEqual([f.text for f in report.findings], ["\"", "\"", ","])
        self.assertEqual([f.start for f in report.findings], [2, 5, 6])
        self.assertEqual(report.findings[2].confusable_with, "，")
        for finding in report.findings:
            self.assertEqual(source[finding.start:finding.end], finding.text)

    def test_fullwidth_punct_inside_ascii_text_flagged(self):
        report = audit_text("hello, world！ok")
        self.assertEqual([f.category for f in report.findings], ["PUNCT_VARIANT"])
        self.assertEqual(report.findings[0].text, "！")
        self.assertEqual(report.findings[0].confusable_with, "!")
        # the ASCII comma is the dominant script here: not flagged
        self.assertEqual([f.start for f in report.findings], [12])

    def test_dominant_script_punct_not_flagged(self):
        self.assertEqual(audit_text("你好，世界！").findings, ())
        self.assertEqual(audit_text('a "quoted" comma, colon: ok?').findings, ())

    def test_classify_stays_context_free(self):
        # PUNCT_VARIANT is decided per string by the scanner, never by classify()
        self.assertIsNone(classify(","))
        self.assertIsNone(classify("，"))

    def test_policy_can_turn_punct_variant_off(self):
        resolved = resolve_policy("neutral")
        del resolved["PUNCT_VARIANT"]
        report = audit_text("他说\"你好\", 然后走了", policy=resolved)
        self.assertEqual(report.findings, ())

    def test_counts_as_info_category(self):
        self.assertIn("PUNCT_VARIANT", INFO_CATEGORIES)
        self.assertIn("FULLWIDTH_HALF", INFO_CATEGORIES)

    def test_sorted_and_non_overlapping_with_other_findings(self):
        report = audit_text("你好,世界\u200b和平")
        categories = [(f.start, f.end) for f in report.findings]
        self.assertEqual(categories, sorted(categories))
        for prev, curr in zip(report.findings, report.findings[1:]):
            self.assertLessEqual(prev.end, curr.start)
        self.assertEqual(
            [f.category for f in report.findings], ["PUNCT_VARIANT", "ZERO_WIDTH"]
        )

    def test_twin_table_is_total_for_flagged_sets(self):
        from charaudit._tables import ASCII_PUNCT_IN_CJK, FULLWIDTH_PUNCT_IN_ASCII

        for ch in ASCII_PUNCT_IN_CJK + FULLWIDTH_PUNCT_IN_ASCII:
            self.assertIn(ch, PUNCT_TWIN)


class TestAuditCorpus(unittest.TestCase):
    def test_yields_reports_in_order_with_policy_name(self):
        texts = ["clean one", "mid\u200bdle", "ＥＮＤ"]
        reports = list(audit_corpus(texts, policy="balanced"))
        self.assertEqual([r.source for r in reports], texts)
        self.assertEqual([r.policy for r in reports], ["balanced"] * 3)
        self.assertEqual(reports[1].stats(), {"ZERO_WIDTH": 1})
        self.assertEqual(reports[2].stats(), {"FULLWIDTH_HALF": 1})

    def test_is_a_lazy_iterator(self):
        def counting():
            counted.append(1)
            yield "x"

        counted: list[int] = []
        stream = audit_corpus(counting())
        self.assertIsInstance(stream, Iterator)
        self.assertEqual(counted, [])  # nothing consumed before iteration starts
        next(stream)
        self.assertEqual(counted, [1])

    def test_bad_policy_fails_before_consuming(self):
        def boom():  # generator: body (and the trap) runs only if consumed
            raise AssertionError("iterable must not be consumed")
            yield "x"  # noqa: unreachable - makes this a generator

        with self.assertRaises(ValueError):
            audit_corpus(boom(), policy="nuclear")

    def test_type_error_propagates_per_item(self):
        with self.assertRaises(TypeError):
            list(audit_corpus([b"bytes"]))

    def test_empty_iterable(self):
        self.assertEqual(list(audit_corpus([])), [])


if __name__ == "__main__":
    unittest.main()
