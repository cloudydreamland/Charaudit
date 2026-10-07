"""Tests for the HOMOGLYPH_UN / HOMOGLYPH_CJK tables and their audit behavior."""
from __future__ import annotations

import hashlib
import importlib
import json
import unittest
from pathlib import Path

import charaudit
from charaudit import (
    CONFUSABLES_VERSION,
    SUSPICIOUS_CATEGORIES,
    TABLE_FINGERPRINTS,
    TABLE_VERSION,
    UNICODE_VERSION,
    audit_prompt,
    audit_text,
    diff_visible,
    resolve_policy,
    sanitize,
)
from charaudit._tables import (
    HOMOGLYPH_CJK,
    HOMOGLYPH_UN,
    classify,
    homoglyph_targets,
    is_invisible,
)

DATA_DIR = Path(charaudit.__file__).parent / "data"
CYRILLIC_ES = "\u0441"  # с, looks like c
GREEK_OMICRON = "\u039f"  # Ο, looks like O


class TestTableContents(unittest.TestCase):
    def test_cyrillic_es_maps_to_c(self):
        self.assertEqual(homoglyph_targets(CYRILLIC_ES), "c")

    def test_greek_omicron_maps_to_O(self):
        self.assertEqual(homoglyph_targets(GREEK_OMICRON), "O")

    def test_cjk_groups(self):
        self.assertEqual(homoglyph_targets("己"), "已/巳")
        self.assertEqual(homoglyph_targets("末"), "未")
        self.assertEqual(homoglyph_targets("士"), "土")

    def test_no_ascii_sources(self):
        for ch in HOMOGLYPH_UN:
            self.assertGreaterEqual(ord(ch), 0x80)

    def test_fullwidth_reserved_for_other_category(self):
        # fullwidth forms belong to the future FULLWIDTH_HALF (INFO) category
        self.assertNotIn(chr(0xFF21), HOMOGLYPH_UN)
        self.assertNotIn(chr(0xFF41), HOMOGLYPH_UN)

    def test_un_table_holds_no_cjk(self):
        for ch in HOMOGLYPH_UN:
            self.assertFalse(0x2E80 <= ord(ch) <= 0x9FFF)

    def test_cjk_chars_inside_unified_block(self):
        self.assertTrue(HOMOGLYPH_CJK)
        for ch in HOMOGLYPH_CJK:
            self.assertTrue(0x3400 <= ord(ch) <= 0x9FFF, f"U+{ord(ch):04X}")

    def test_sizes_match_recorded_provenance(self):
        meta = json.loads((DATA_DIR / "confusables_un.json").read_text(encoding="utf-8"))["_meta"]
        cjk_meta = json.loads((DATA_DIR / "cjk_confusables.json").read_text(encoding="utf-8"))["_meta"]
        self.assertEqual(len(HOMOGLYPH_UN), meta["counts"]["kept_sources"])
        self.assertGreater(len(HOMOGLYPH_UN), 1000)
        self.assertEqual(cjk_meta["group_count"], 250)
        self.assertEqual(cjk_meta["char_count"], len(HOMOGLYPH_CJK))


class TestClassify(unittest.TestCase):
    def test_cyrillic_and_greek(self):
        self.assertEqual(classify(CYRILLIC_ES), "HOMOGLYPH_UN")
        self.assertEqual(classify(GREEK_OMICRON), "HOMOGLYPH_UN")

    def test_cjk(self):
        for ch in ("己", "已", "巳", "末", "未", "士"):
            self.assertEqual(classify(ch), "HOMOGLYPH_CJK")

    def test_plain_chars_stay_benign(self):
        for ch in ("c", "O", "1", "l", "I", "a", "平", "安"):
            self.assertIsNone(classify(ch))

    def test_range_classes_keep_priority(self):
        self.assertEqual(classify("\u200b"), "ZERO_WIDTH")
        self.assertEqual(classify("\u202e"), "BIDI")
        self.assertEqual(classify("\u0085"), "CONTROL")

    def test_homoglyphs_are_visible_not_invisible(self):
        self.assertFalse(is_invisible(CYRILLIC_ES))
        self.assertFalse(is_invisible("己"))
        self.assertTrue(is_invisible("\u200b"))


class TestAuditVectors(unittest.TestCase):
    def test_spoofed_english_word(self):
        source = "s" + CYRILLIC_ES + "ure"  # looks exactly like "secure"
        report = audit_text(source)
        self.assertEqual([f.category for f in report.findings], ["HOMOGLYPH_UN"])
        finding = report.findings[0]
        self.assertEqual(finding.start, 1)
        self.assertEqual(finding.codepoint, "U+0441")
        self.assertIn("CYRILLIC SMALL LETTER ES", finding.unicode_name)
        self.assertEqual(finding.risk, "SUSPICIOUS")
        self.assertEqual(finding.suggestion, "REVIEW")
        self.assertEqual(finding.confusable_with, "c")
        self.assertEqual(source[finding.start:finding.end], finding.text)

    def test_adjacent_homoglyph_runs_merge(self):
        report = audit_text(CYRILLIC_ES + GREEK_OMICRON + "re")
        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertEqual((finding.start, finding.end), (0, 2))
        self.assertEqual(finding.confusable_with, "cO")

    def test_cjk_vector(self):
        source = "知己知彼"  # only 己 is a curated confusable here
        report = audit_text(source)
        self.assertEqual([f.category for f in report.findings], ["HOMOGLYPH_CJK"])
        finding = report.findings[0]
        self.assertEqual(finding.start, 1)
        self.assertEqual(finding.confusable_with, "已/巳")
        self.assertIn("review hint", finding.note)

    def test_prompt_policy_flags_suspicious(self):
        report = audit_prompt("pa" + "\u0430" + "ypal.com")  # Cyrillic а
        self.assertEqual(report.findings[0].category, "HOMOGLYPH_UN")
        self.assertEqual(report.findings[0].risk, "SUSPICIOUS")
        self.assertEqual(report.findings[0].suggestion, "REVIEW")


class TestPolicyAndSanitize(unittest.TestCase):
    def test_all_presets_flag_homoglyphs_suspicious(self):
        for preset in ("strict", "balanced", "neutral"):
            resolved = resolve_policy(preset)
            for category in SUSPICIOUS_CATEGORIES:
                self.assertEqual(resolved[category], ("SUSPICIOUS", "REVIEW"), preset)

    def test_unknown_custom_category_rejected(self):
        with self.assertRaises(ValueError):
            resolve_policy({"HOMOGLYPH_NOPE": ("FORBIDDEN", "REMOVE")})

    def test_strict_sanitize_keeps_homoglyphs(self):
        cleaned, log = sanitize("s" + CYRILLIC_ES + "ure")
        self.assertEqual(cleaned, "s" + CYRILLIC_ES + "ure")
        self.assertEqual(log.changes, ())

    def test_custom_policy_can_remove_homoglyphs(self):
        cleaned, log = sanitize(
            "s" + CYRILLIC_ES + "ure",
            policy={"HOMOGLYPH_UN": ("SUSPICIOUS", "REMOVE")},
        )
        # delete-only: the confusable is removed, never substituted by "c"
        self.assertEqual(cleaned, "sure")
        self.assertEqual(len(log.changes), 1)
        change = log.changes[0]
        self.assertEqual((change.start, change.end, change.removed), (1, 2, CYRILLIC_ES))
        self.assertEqual(change.category, "HOMOGLYPH_UN")

    def test_custom_policy_can_promote_to_forbidden(self):
        report = audit_text(
            "自" + "己",
            policy={"HOMOGLYPH_CJK": ("FORBIDDEN", "REMOVE")},
        )
        self.assertEqual(report.findings[0].risk, "FORBIDDEN")


class TestDiffIntegration(unittest.TestCase):
    def test_homoglyph_difference_is_visible(self):
        report = diff_visible("s" + CYRILLIC_ES + "ure", "secure")
        self.assertFalse(report.equal)
        # с is a visible character: the visible sequences genuinely differ
        self.assertFalse(report.equal_visible)
        ops = [s.op for s in report.segments if s.op != "equal"]
        self.assertEqual(ops, ["visible"])
        explanation = report.explain()
        self.assertIn("可见内容差异", explanation)
        self.assertIn("易混淆字符", explanation)
        self.assertIn("U+0441", explanation)
        self.assertIn("≈c", explanation)

    def test_invisible_diff_unchanged(self):
        report = diff_visible("订阅成功", "订阅成\u200b功")
        self.assertTrue(report.equal_visible)
        self.assertIn("可见内容一致", report.explain())


class TestFingerprintsAndVersions(unittest.TestCase):
    def test_fingerprints_match_shipped_files(self):
        for name, digest in TABLE_FINGERPRINTS.items():
            raw = (DATA_DIR / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest, name)

    def test_meta_map_sha256_covers_mapping_canonically(self):
        for filename, section in (
            ("confusables_un.json", "map"),
            ("cjk_confusables.json", "mates"),
        ):
            doc = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
            canonical = json.dumps(
                doc[section], sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            self.assertEqual(
                hashlib.sha256(canonical).hexdigest(),
                doc["_meta"]["map_sha256"],
                filename,
            )

    def test_table_version_records_all_sources(self):
        self.assertEqual(
            TABLE_VERSION,
            f"2026.10-unicode{UNICODE_VERSION}+confusables{CONFUSABLES_VERSION}",
        )
        self.assertEqual(CONFUSABLES_VERSION, "18.0.0")
        report = audit_text(CYRILLIC_ES)
        self.assertEqual(report.table_version, TABLE_VERSION)

    def test_reload_gives_identical_fingerprints(self):
        before = dict(TABLE_FINGERPRINTS)
        importlib.reload(importlib.import_module("charaudit._tables"))
        import charaudit as reloaded

        self.assertEqual(dict(reloaded.TABLE_FINGERPRINTS), before)


if __name__ == "__main__":
    unittest.main()
