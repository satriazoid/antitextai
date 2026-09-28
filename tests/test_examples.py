"""The documented example is part of the contract, not decoration.

`examples/demo_before.md` carries every tell the tool claims to remove. If a rule change makes
the cleaner disagree with `examples/demo_after.md`, this test fails and the README is wrong.
"""
import pathlib
import unittest

from antitextai import clean, verify_text

ROOT = pathlib.Path(__file__).resolve().parent.parent
BEFORE = ROOT / "examples" / "demo_before.md"
AFTER = ROOT / "examples" / "demo_after.md"


def read(path):
    return path.read_text(encoding="utf-8")


class ExampleFixtureTest(unittest.TestCase):
    def test_fixture_is_present_and_dirty(self):
        self.assertTrue(BEFORE.is_file(), "examples/demo_before.md is missing")
        reason = verify_text(read(BEFORE))
        self.assertIsNotNone(reason, "the before-fixture is no longer dirty; it proves nothing")
        self.assertIn("INVISIBLE", reason or "")

    def test_cleaner_reproduces_the_documented_output_byte_for_byte(self):
        got = clean(read(BEFORE)).encode("utf-8")
        self.assertEqual(got, AFTER.read_bytes(),
                         "examples/demo_after.md drifted from what clean() produces")

    def test_documented_output_is_clean_apart_from_reviewed_dashes(self):
        reason = verify_text(read(AFTER))
        self.assertIsNotNone(reason)          # dashes stay, so the note is expected
        self.assertIn("dash review", reason or "")

    def test_documented_output_is_idempotent(self):
        self.assertEqual(clean(read(AFTER)), read(AFTER))


if __name__ == "__main__":
    unittest.main(verbosity=2)
