"""End-to-end tests for the command line: exit codes, --write, stdin, --json."""
import io
import json
import pathlib
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from antitextai.cli import main


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.dirty = self.root / "draft.md"
        # Bytes, not write_text: Python would translate \n to \r\n on Windows and the
        # cleaner would then (correctly) preserve CRLF, making the assertions platform-bound.
        self.dirty.write_bytes("\ufeffCertainly! Here\u200b is the plan.\n\nHope this helps!\n"
                               .encode("utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_command_prints_help(self):
        code, out, _ = run([])
        self.assertEqual(code, 0)
        self.assertIn("usage: antitextai", out)

    def test_scan_reports_without_touching_the_file(self):
        before = self.dirty.read_bytes()
        code, out, _ = run(["scan", str(self.root)])
        self.assertEqual(code, 0)          # default is report-only
        self.assertIn("U+200B", out)
        self.assertEqual(self.dirty.read_bytes(), before)

    def test_scan_strict_exits_one(self):
        code, _, _ = run(["scan", str(self.root), "--strict", "--json"])
        self.assertEqual(code, 1)

    def test_scan_json_is_parseable(self):
        _, out, _ = run(["scan", str(self.root), "--json"])
        payload = json.loads(out)
        self.assertIsInstance(payload, list)
        self.assertEqual(len(payload), 1)
        self.assertIn("chars", payload[0])

    def test_clean_prints_to_stdout_by_default(self):
        code, out, _ = run(["clean", str(self.dirty), "--quiet"])
        self.assertEqual(code, 0)
        self.assertIn("Here is the plan.", out)
        self.assertNotIn("Certainly", out)
        self.assertIn("\ufeff", self.dirty.read_text(encoding="utf-8"))  # untouched

    def test_clean_write_rewrites_in_place_and_keeps_utf8(self):
        code, _, err = run(["clean", "--write", str(self.dirty)])
        self.assertEqual(code, 0)
        self.assertIn("cleaned", err)
        written = self.dirty.read_bytes()
        self.assertFalse(written.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\xe2\x80\x8b", written)
        self.assertEqual(self.dirty.read_text(encoding="utf-8"),
                         "Here is the plan.\n")

    def test_clean_write_is_idempotent(self):
        run(["clean", "--write", str(self.dirty)])
        first = self.dirty.read_bytes()
        code, _, _ = run(["clean", "--write", str(self.dirty)])
        self.assertEqual(code, 0)
        self.assertEqual(self.dirty.read_bytes(), first)

    def test_clean_stdin_to_stdout(self):
        import sys
        old = sys.stdin
        sys.stdin = io.StringIO("Certainly! The build passes.\n")
        try:
            code, out, _ = run(["clean", "-"])
        finally:
            sys.stdin = old
        self.assertEqual(code, 0)
        self.assertEqual(out, "The build passes.\n")

    def test_verify_strict_fails_before_and_passes_after(self):
        code, out, _ = run(["verify", str(self.root), "--strict"])
        self.assertEqual(code, 1)
        self.assertIn("dirty", out)
        run(["clean", "--write", str(self.dirty)])
        code, out, _ = run(["verify", str(self.root), "--strict"])
        self.assertEqual(code, 0)
        self.assertIn("0 still dirty", out)

    def test_verify_allow_dashes(self):
        dash = self.root / "ranges.md"
        dash.write_bytes("Range 2019\u20132021.\n".encode("utf-8"))
        self.assertEqual(run(["verify", str(dash), "--strict"])[0], 1)
        self.assertEqual(run(["verify", str(dash), "--strict", "--allow-dashes"])[0], 0)

    def test_no_bom_flag_keeps_the_bom(self):
        code, out, _ = run(["clean", str(self.dirty), "--no-bom", "--quiet"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("\ufeff"))

    def test_missing_file_is_a_clean_noop(self):
        code, out, _ = run(["scan", str(self.root / "nope.md")])
        self.assertEqual(code, 0)
        self.assertIn("0 of 0 files", out)

    def test_version(self):
        with self.assertRaises(SystemExit) as ctx:
            run(["--version"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
