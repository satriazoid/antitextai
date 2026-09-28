"""Tests for the proof pass: the verifier must agree with the cleaner exactly."""
import pathlib
import tempfile
import unittest

from antitextai import clean
from antitextai.verify import format_report, verify_paths, verify_text


class VerifyTextTest(unittest.TestCase):
    def test_clean_text_passes(self):
        self.assertIsNone(verify_text("Plain sentence.\n"))

    def test_output_of_clean_always_passes(self):
        dirty = "\ufeffCertainly! Here\u200b is the fix:\n\nHope this helps!\n"
        self.assertIsNone(verify_text(clean(dirty)))

    def test_residual_invisible_is_reported(self):
        reason = verify_text("word\u200b join\n")
        self.assertIsNotNone(reason)
        self.assertIn("INVISIBLE", reason or "")

    def test_residual_separator_is_reported(self):
        reason = verify_text("# ==========\n")
        self.assertIsNotNone(reason)
        self.assertIn("SEPARATOR", reason or "")

    def test_dash_needs_review(self):
        reason = verify_text("Range 2019\u20132021 stays.\n")
        self.assertIsNotNone(reason)
        self.assertIn("dash review", reason or "")


class VerifyPathsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "clean.md").write_bytes(b"Fine text.\n")
        (self.root / "dirty.md").write_bytes("Fine\u200b text.\n".encode("utf-8"))
        # A .txt name so the extension filter keeps it, with NUL bytes so read_text drops it.
        (self.root / "blob.txt").write_bytes(b"\x00\x01\x02")

    def tearDown(self):
        self.tmp.cleanup()

    def test_statuses(self):
        reports = {r["path"].split("\\")[-1].split("/")[-1]: r
                   for r in verify_paths([str(self.root)])}
        self.assertEqual(reports["clean.md"]["status"], "clean")
        self.assertEqual(reports["dirty.md"]["status"], "dirty")
        self.assertIn("INVISIBLE", reports["dirty.md"]["detail"])
        self.assertEqual(reports["blob.txt"]["status"], "skipped")

    def test_strict_style_reporting(self):
        out = format_report(verify_paths([str(self.root)]))
        self.assertIn("dirty.md", out)
        self.assertNotIn("clean.md", out)
        self.assertIn("1 still dirty", out)

    def test_show_clean_lists_everything(self):
        out = format_report(verify_paths([str(self.root)]), show_clean=True)
        self.assertIn("clean.md", out)

    def test_allow_dashes_silences_the_note_only(self):
        (self.root / "dash.md").write_bytes("Range 2019\u20132021.\n".encode("utf-8"))
        strict = {r["path"] for r in verify_paths([str(self.root)]) if r["status"] == "dirty"}
        lenient = {r["path"] for r in verify_paths([str(self.root)], allow_dashes=True)
                   if r["status"] == "dirty"}
        self.assertTrue(any(p.endswith("dash.md") for p in strict))
        self.assertFalse(any(p.endswith("dash.md") for p in lenient))


if __name__ == "__main__":
    unittest.main(verbosity=2)
