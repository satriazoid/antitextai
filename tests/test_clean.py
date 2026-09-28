"""Regression suite for the deterministic cleaner.

Every assertion here is a defect that was actually observed during construction, not a
hypothetical: content-destroying frame rules, orphaned words from non-atomic openers,
setext headings eaten by the separator rule, trailing end-markers deleting code, CRLF
rewritten as LF. Run with `python -m unittest discover -s tests -t .` or `pytest`.
"""
import unittest

from antitextai.cleaner import assert_no_artifacts, clean

DIRTY = (
    "\ufeffCertainly! Here's a breakdown\u200b of the code.\n"
    "In today's fast-paced digital landscape, teams ship faster.\n"
    "\n"
    "It's important to note that the loop terminates. That said, we keep it.\n"
    "\n"
    "Here is the complete Python script to achieve this:\n"
    "\n"
    "```python\n"
    "-- Increment counter by 1\n"
    "counter\u00a0+=\u00a01\n"
    "-- Step 1: initialize the list\n"
    "results = []\u00a0\u2022 extra\n"
    "# ==========================================\n"
    "# HELPER FUNCTIONS\n"
    "# ==========================================\n"
    "def add(a, b):\n"
    "    return a + b  # end function add\n"
    "-- now, we emit the result\n"
    "print(add(1, 2))\n"
    "\n"
    "# end of function add\n"
    "```\n"
    "\n"
    "The API\u2014which is v2\u20132019\u2014is used \u201chere\u201d.  \n"
    "Note = \"# end of loop\"\n"
    "List:\u2022 alpha\u2022 beta\u2026  \n"
    "\n"
    "Let me know if you'd like more detail.\n"
    "\n"
    "\n"
    "End.\n"
)

# Framing is removed; the substance it wrapped is KEPT and recapitalized.
EXPECTED = (
    "Here's a breakdown of the code.\n"
    "Teams ship faster.\n"
    "\n"
    "The loop terminates. We keep it.\n"
    "\n"
    "```python\n"
    "-- Increment counter by 1\n"
    "counter += 1\n"
    "results = [] - extra\n"
    "# HELPER FUNCTIONS\n"
    "def add(a, b):\n"
    "    return a + b\n"
    "print(add(1, 2))\n"
    "\n"
    "```\n"
    "\n"
    'The API\u2014which is v2\u20132019\u2014is used "here".\n'
    'Note = "# end of loop"\n'
    "List:- alpha- beta...\n"
    "\n"
    "End.\n"
)

MARKDOWN = (
    '---\nname: demo\ndescription: "smart \u2014 quotes stay"\n---\n'
    "\n"
    "Certainly! Here is the guide.\n"
    "\n"
    "## Overview\n"
    "\n"
    "Text\u00a0with NBSP\u200b and \u201cquotes\u201d\u2026\n"
)

CODE_SAFETY = (
    'a = "# end of loop"\n'
    'b = "------"\n'
    'c = "it\'s important to note that x"\n'
    "i -= 1\n"
    "url = 'http://x--y/z'\n"
)


class CleanDocumentTest(unittest.TestCase):
    def test_mixed_document(self):
        got = clean(DIRTY)
        self.assertEqual(got, EXPECTED, f"clean() drift:\n--- got ---\n{got!r}")
        assert_no_artifacts(got)

    def test_idempotent(self):
        once = clean(DIRTY)
        self.assertEqual(clean(once), once)

    def test_frontmatter_is_byte_identical(self):
        out = clean(MARKDOWN)
        self.assertTrue(out.startswith(
            '---\nname: demo\ndescription: "smart \u2014 quotes stay"\n---\n'), out)
        self.assertNotIn("Certainly", out)
        self.assertIn("Here is the guide.", out)
        self.assertNotIn("\u201cquotes\u201d", out)
        self.assertIn("...", out)
        self.assertNotIn("\u00a0", out)
        self.assertNotIn("\u200b", out)
        assert_no_artifacts(out)
        self.assertEqual(clean(out), out, "not idempotent (md)")

    def test_code_strings_and_operators_untouched(self):
        self.assertEqual(clean(CODE_SAFETY), CODE_SAFETY)


class FrameTest(unittest.TestCase):
    """Frames wrap substance: strip the frame, keep the sentence, recapitalize."""

    def test_adverbial_opener(self):
        self.assertEqual(clean("In today's market, revenue grew 12%.\n"),
                         "Revenue grew 12%.\n")

    def test_interjection(self):
        self.assertEqual(clean("Certainly! The build passes.\n"), "The build passes.\n")

    def test_multi_word_openers_are_atomic(self):
        # Matching a bare `sure` once produced the orphan "Thing! Below is a walkthrough."
        self.assertEqual(clean("Sure thing! Below is a walkthrough.\n"),
                         "Below is a walkthrough.\n")
        self.assertEqual(clean("No problem! Here is the fix.\n"), "Here is the fix.\n")

    def test_opener_without_punctuation_is_content(self):
        self.assertEqual(clean("Got it working now.\n"), "Got it working now.\n")

    def test_pure_signoff_vanishes(self):
        self.assertEqual(clean("Hope this helps!\n"), "")

    def test_precode_meta_text(self):
        self.assertEqual(clean("Here is the fix:\nx = 1\n"), "x = 1\n")

    def test_subordinate_clause_keeps_the_clause(self):
        self.assertEqual(clean("It's important to note that the loop terminates.\n"),
                         "The loop terminates.\n")
        self.assertEqual(clean("Note that retries are capped.\n"), "Retries are capped.\n")

    def test_mid_paragraph_gesture(self):
        self.assertEqual(clean("Caching is essential. Please note that TTLs prevent staleness.\n"),
                         "Caching is essential. TTLs prevent staleness.\n")
        self.assertEqual(clean("Done. Note that retries are capped.\n"),
                         "Done. Retries are capped.\n")


class CodeAndStructureTest(unittest.TestCase):
    def test_setext_underline_survives(self):
        document = "Legacy Heading\n--------------\n\nBody.\n"
        self.assertEqual(clean(document), document)

    def test_real_banner_still_removed(self):
        self.assertEqual(clean("# ==========\n# IMPORTS\n# ==========\nimport os\n"),
                         "# IMPORTS\nimport os\n")

    def test_trailing_end_marker_drops_comment_only(self):
        self.assertEqual(clean("def f():\n    return 1  # end function f\n"),
                         "def f():\n    return 1\n")

    def test_inline_signoff_stripped_sentence_survives(self):
        self.assertEqual(clean("FastAPI is a solid choice. Hope this helps!"),
                         "FastAPI is a solid choice.\n")

    def test_mid_sentence_data_is_not_a_signoff(self):
        sentence = "The flag will let me know if the job fails."
        self.assertEqual(clean(sentence), sentence + "\n")

    def test_line_endings_preserved(self):
        self.assertEqual(clean("Certainly! Done.\r\n\r\nBody\u00a0here.\r\n"),
                         "Done.\r\n\r\nBody here.\r\n")
        self.assertEqual(clean("Alpha. Hope this helps!"), "Alpha.\n")

    def test_em_dash_never_touched(self):
        text = "Ranges 2019\u20132021 and clauses \u2014 both stay.\n"
        self.assertEqual(clean(text), text)

    def test_strip_bom_can_be_disabled(self):
        self.assertEqual(clean("\ufeffHi.\n", strip_bom=False), "\ufeffHi.\n")
        self.assertEqual(clean("\ufeffHi.\n"), "Hi.\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
