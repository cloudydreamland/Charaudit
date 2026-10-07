"""Tests for sanitize and diff_visible."""
from __future__ import annotations

import random
import unittest

from charaudit import ChangeLog, diff_visible, sanitize
from charaudit._tables import classify, is_invisible


class TestSanitize(unittest.TestCase):
    def test_basic_removal_with_original_offsets(self):
        text = "_ignore\u200bprev\u202erules"
        cleaned, log = sanitize(text)
        self.assertEqual(cleaned, "_ignoreprevrules")
        self.assertEqual(len(log.changes), 2)
        first, second = log.changes
        self.assertEqual((first.start, first.end, first.removed), (7, 8, "\u200b"))
        self.assertEqual(first.category, "ZERO_WIDTH")
        self.assertEqual((second.start, second.end, second.removed), (12, 13, "\u202e"))
        self.assertEqual(second.category, "BIDI")
        self.assertEqual(log.source_length, len(text))

    def test_removed_offsets_invariant_and_reconstruction(self):
        rng = random.Random(20261007)
        alphabet = (
            "中文字符串测试abc123"
            + "\u200b\u2060\u202e\ud800\x1b\x00\U000e0030"
            + "с己"  # homoglyphs are REVIEW under strict: flagged, never removed
        )
        for case in range(200):
            source = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 60)))
            with self.subTest(case=case):
                cleaned, log = sanitize(source)
                # every change points back into the original text
                for change in log.changes:
                    self.assertEqual(
                        source[change.start : change.end], change.removed
                    )
                    for ch in change.removed:
                        self.assertIsNotNone(classify(ch))
                # removing all change ranges from the source rebuilds the cleaned text
                rebuilt = list(source)
                for change in sorted(log.changes, key=lambda c: c.start, reverse=True):
                    del rebuilt[change.start : change.end]
                self.assertEqual("".join(rebuilt), cleaned)
                self.assertEqual(log.source_length, len(source))

    def test_neutral_policy_is_noop(self):
        text = "keep\u200bme"
        cleaned, log = sanitize(text, policy="neutral")
        self.assertEqual(cleaned, text)
        self.assertEqual(log.changes, ())
        self.assertEqual(log.rounds, 1)

    def test_balanced_keeps_control(self):
        cleaned, log = sanitize("a\x00b\u200bc", policy="balanced")
        self.assertEqual(cleaned, "a\x00bc")
        self.assertEqual(log.summary(), {"ZERO_WIDTH": 1})

    def test_surrogate_removal_enables_utf8(self):
        cleaned, _ = sanitize("a\ud800b")
        self.assertEqual(cleaned, "ab")
        cleaned.encode("utf-8")  # the original text cannot be UTF-8 encoded

    def test_utf16_roundtrip_stability_and_rounds(self):
        cleaned, log = sanitize("\u200b\u2060\u202e\U000e0030\ud800中文")
        self.assertEqual(cleaned, "中文")
        # rounds counts audit passes: one removal pass + one final no-op pass
        self.assertEqual(log.rounds, 2)
        roundtrip = cleaned.encode("utf-16", "surrogatepass").decode(
            "utf-16", "surrogatepass"
        )
        self.assertEqual(roundtrip, cleaned)

    def test_empty_text(self):
        cleaned, log = sanitize("")
        self.assertEqual(cleaned, "")
        self.assertEqual(log, ChangeLog((), 0, 1))

    def test_bytes_rejected(self):
        with self.assertRaises(TypeError):
            sanitize(b"\x00")


class TestDiffVisible(unittest.TestCase):
    def test_identical(self):
        report = diff_visible("订阅成功", "订阅成功")
        self.assertTrue(report.equal)
        self.assertTrue(report.equal_visible)
        self.assertIn("完全相同", report.explain())

    def test_invisible_only_in_b(self):
        report = diff_visible("订阅成功", "订阅成\u200b功")
        self.assertFalse(report.equal)
        self.assertTrue(report.equal_visible)
        diff_segments = [s for s in report.segments if s.op != "equal"]
        self.assertEqual(len(diff_segments), 1)
        self.assertEqual(diff_segments[0].op, "invisible")
        self.assertEqual(diff_segments[0].hidden_b, "\u200b")
        explanation = report.explain()
        self.assertIn("可见内容一致", explanation)
        self.assertIn("U+200B", explanation)

    def test_invisible_only_in_a(self):
        report = diff_visible("api\u200bkey", "apikey")
        self.assertTrue(report.equal_visible)
        diff_segments = [s for s in report.segments if s.op != "equal"]
        self.assertEqual(len(diff_segments), 1)
        self.assertEqual(diff_segments[0].hidden_a, "\u200b")

    def test_visible_diff(self):
        report = diff_visible("你好", "再见")
        self.assertFalse(report.equal_visible)
        self.assertIn("可见内容差异", report.explain())
        self.assertTrue(any(s.op == "visible" for s in report.segments))

    def test_different_hidden_categories_both_sides(self):
        report = diff_visible("a\u200bx", "a\u202ex")
        self.assertTrue(report.equal_visible)
        explanation = report.explain()
        self.assertIn("a 侧隐形字符 1 处", explanation)
        self.assertIn("b 侧隐形字符 1 处", explanation)

    def test_segments_reconstruct_inputs(self):
        rng = random.Random(20261007)
        alphabet = "中文visible abcс己已" + "\u200b\u2060\u202e\ud800\x00"
        for case in range(200):
            a = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 40)))
            b = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 40)))
            with self.subTest(case=case):
                report = diff_visible(a, b)
                self.assertEqual("".join(s.text_a for s in report.segments), a)
                self.assertEqual("".join(s.text_b for s in report.segments), b)
                visible_a = [ch for ch in a if not is_invisible(ch)]
                visible_b = [ch for ch in b if not is_invisible(ch)]
                self.assertEqual(report.equal_visible, visible_a == visible_b)

    def test_bytes_rejected(self):
        with self.assertRaises(TypeError):
            diff_visible(b"a", "a")


if __name__ == "__main__":
    unittest.main()
