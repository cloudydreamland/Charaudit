"""Offset-invariant and coverage fuzz tests (seeded, deterministic)."""
from __future__ import annotations

import random
import unittest

from charaudit import audit_text
from charaudit._tables import classify

BENIGN = "中文字符串测abcXYZ019 3.14、。！"
INVISIBLE = "\u200b\u200c\u200d\u2060\u202e\u2066\U000e0030\U000e007f\ud800\x00\x1b\x85\x7f"
HOMOGLYPH = "сο\u0430己已巳末未土士"


class TestOffsetInvariantFuzz(unittest.TestCase):
    def test_fuzz_invariants(self):
        rng = random.Random(20261007)
        for case in range(300):
            length = rng.randrange(0, 80)
            source = "".join(
                rng.choice(BENIGN)
                if rng.random() < 0.7
                else rng.choice(rng.choice((INVISIBLE, HOMOGLYPH)))
                for _ in range(length)
            )
            with self.subTest(case=case):
                report = audit_text(source, policy="strict")
                findings = report.findings
                # 1. offset invariant holds for every finding
                for f in findings:
                    self.assertEqual(source[f.start : f.end], f.text)
                    for ch in f.text:
                        self.assertEqual(classify(ch), f.category)
                # 2. findings ordered, non-overlapping (adjacent categories may touch)
                for prev, curr in zip(findings, findings[1:]):
                    self.assertLessEqual(prev.end, curr.start)
                # 3. coverage: every flagged code point is inside exactly one finding
                covered = [cp for f in findings for cp in range(f.start, f.end)]
                expected = [i for i, ch in enumerate(source) if classify(ch) is not None]
                self.assertEqual(covered, expected)
                # 4. benign positions never flagged
                flagged = set(covered)
                for i, ch in enumerate(source):
                    if classify(ch) is None:
                        self.assertNotIn(i, flagged)


if __name__ == "__main__":
    unittest.main()
