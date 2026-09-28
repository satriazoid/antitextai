"""Tests for the inventory pass: classification, rule hits, and file walking."""
import json
import os
import pathlib
import tempfile
import unittest

from antitextai import scan_text
from antitextai.files import is_probably_text, iter_files, read_text
from antitextai.scan import char_report, format_report, rule_report, scan_paths


class CharReportTest(unittest.TestCase):
    def test_categories(self):
        text = ("word\u200b joins\n"
                "smart \u201cquotes\u201d and \u2026\n"
                "dash \u2014 review me\n"
                "range 2019\u20132021\n"
                "box \u2500\u2500 banner\n"
                "keep \u03a3 and \u00b1 and \u00e9\n")
        got = {(c["codepoint"], c["category"]) for c in char_report(text)}
        self.assertIn(("U+200B", "mapped"), got)
        self.assertIn(("U+201C", "mapped"), got)
        self.assertIn(("U+2026", "mapped"), got)
        self.assertIn(("U+2014", "review"), got)
        self.assertIn(("U+2013", "review"), got)
        self.assertIn(("U+2500", "decorative"), got)
        self.assertIn(("U+03A3", "keep"), got)
        self.assertIn(("U+00B1", "keep"), got)
        self.assertIn(("U+00E9", "keep"), got)

    def test_counts_and_first_location(self):
        entries = {c["codepoint"]: c for c in char_report("a\u200bb\u200b\nc\u00a0d\n")}
        self.assertEqual(entries["U+200B"]["count"], 2)
        self.assertEqual(entries["U+200B"]["first"], "1:2")
        self.assertEqual(entries["U+00A0"]["first"], "2:2")

    def test_ascii_only_text_reports_nothing(self):
        self.assertEqual(char_report("plain ascii\n"), [])


class RuleReportTest(unittest.TestCase):
    def test_interjection_and_separator_found(self):
        rules = {r["rule"]: r for r in rule_report("Certainly! Go.\n# ==========\n")}
        self.assertIn("INTERJECT", rules)
        self.assertIn("SEPARATOR", rules)
        self.assertEqual(rules["SEPARATOR"]["count"], 1)

    def test_clean_text_has_no_rule_hits(self):
        self.assertEqual(rule_report("Plain paragraph.\n"), [])

    def test_line_numbers_point_at_the_match(self):
        rules = {r["rule"]: r for r in rule_report("Intro line.\nCertainly! Go.\n# ==========\n")}
        self.assertEqual(rules["INTERJECT"]["lines"], [2])
        self.assertEqual(rules["SEPARATOR"]["lines"], [3])

    def test_line_numbers_count_the_frontmatter(self):
        text = "---\ntitle: x\n---\n\nCertainly! Go.\n"
        rules = {r["rule"]: r for r in rule_report(text)}
        self.assertEqual(rules["INTERJECT"]["lines"], [5])

    def test_scan_text_totals(self):
        # One mapped char, one review char, one decorative char, one rule hit.
        report = scan_text("Certainly! The \u201cAPI\u201d\u2014end \u2500 done.\n")
        self.assertGreaterEqual(report["mapped"], 2)
        self.assertEqual(report["review"], 1)
        self.assertEqual(report["decorative"], 1)
        self.assertGreaterEqual(report["rule_hits"], 1)


class FormatTest(unittest.TestCase):
    def test_summary_line_always_present(self):
        out = format_report([{"path": "a.md", "chars": [], "rules": [], "kinds": 0,
                              "review": 0, "rule_hits": 0}])
        self.assertIn("0 of 1 files carry AI tells", out)

    def test_findings_are_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp, "dirty.md")
            p.write_bytes("Certainly! Go.\u200b\n".encode("utf-8"))
            reports = scan_paths([tmp])
        out = format_report(reports)
        self.assertIn("dirty.md", out)
        self.assertIn("U+200B", out)
        self.assertIn("INTERJECT", out)
        self.assertEqual(reports[0]["path"], str(p))

    def test_line_alone_fluff_is_reported_as_bare_fluff(self):
        rules = {r["rule"] for r in rule_report("Certainly!\n")}
        self.assertIn("BARE_FLUFF", rules)

    def test_invisible_rule_reports_the_character(self):
        rules = {r["rule"]: r for r in rule_report("word\u200b join\n")}
        self.assertIn("INVISIBLE", rules)
        self.assertEqual(rules["INVISIBLE"]["count"], 1)


class FileWalkingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "a.md").write_bytes(b"hi\n")
        (self.root / "docs" / "skip.png").write_bytes(b"\x89PNG\x00\xff")
        (self.root / "node_modules").mkdir()
        (self.root / "node_modules" / "b.md").write_bytes(b"dep\n")
        (self.root / "Makefile").write_bytes(b"all:\n")
        (self.root / "utf16.txt").write_bytes("hi\n".encode("utf-16"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_extension_and_dir_filtering(self):
        # Filtering is by name and extension only; utf16.txt is listed here and
        # dropped later by read_text(), which refuses non-UTF-8 and NUL bytes.
        found = {p.name for p in iter_files([str(self.root)])}
        self.assertEqual(found, {"a.md", "Makefile", "utf16.txt"})

    def test_explicit_file_bypasses_extension_filter(self):
        explicit = self.root / "docs" / "skip.png"
        self.assertIn(explicit, iter_files([str(explicit)]))

    def test_exclude_globs(self):
        found = {p.name for p in iter_files([str(self.root)], exclude_globs=["*.md"])}
        self.assertNotIn("a.md", found)
        self.assertIn("Makefile", found)

    def test_binary_and_non_utf8_detection(self):
        self.assertFalse(is_probably_text(b"\x89PNG\x00"))
        self.assertFalse(is_probably_text("hi\n".encode("utf-16")))
        self.assertTrue(is_probably_text("hi\n".encode("utf-8")))
        self.assertIsNone(read_text(self.root / "utf16.txt"))
        self.assertIsNone(read_text(self.root / "docs" / "skip.png"))
        self.assertEqual(read_text(self.root / "docs" / "a.md"), "hi\n")

    def test_json_output_is_serialisable(self):
        reports = scan_paths([str(self.root)])
        json.dumps(reports)  # raises TypeError on a non-serialisable value


if __name__ == "__main__":
    unittest.main(verbosity=2)
