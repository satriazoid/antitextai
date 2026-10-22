"""Tests for comment spam detection and the comment scrub."""
import unittest

from antitextai.comments import scan_text, scrub_text

NARRATION = """# This function takes the user id and looks up the user
# in the database using a simple query that selects all
# of the columns from the users table where the id
# matches the given id, and then it returns the row
# back to the caller so the caller can use the data
# in whatever way the caller needs to use it today.
def get_user(user_id):
    return db.fetch(user_id)
"""

LICENSE_BLOCK = """# Copyright 2026 Example Project
# Licensed under the Apache License, Version 2.0
# You may not use this file except in compliance
# with the License. You may obtain a copy of the
# License at the usual distribution location.
def main():
    pass
"""

TODO_BLOCK = """# TODO: revisit this once the cache layer lands
# The current approach scans the whole table and
# that will not scale past the current data size,
# but changing it now would break the release.
def scan():
    pass
"""

SHORT_NOTES = """# Cache lives for one request only.
# Nothing here is safe to share across threads.
def build():
    return {}
"""


class ScanCommentsTest(unittest.TestCase):
    def test_long_block_detected(self):
        rules = [f.rule for f in scan_text("a.py", NARRATION)]
        self.assertIn("LONG_COMMENT_BLOCK", rules)

    def test_comment_heavy_file_detected(self):
        block = "\n".join(f"# Explanation line {i} that narrates the obvious." for i in range(6))
        text = f"{block}\ndef a():\n{block}\n    return 1\n"
        rules = [f.rule for f in scan_text("a.py", text)]
        self.assertIn("COMMENT_HEAVY", rules)

    def test_short_comments_are_not_spam(self):
        self.assertEqual(scan_text("a.py", SHORT_NOTES), [])

    def test_long_comment_line_detected(self):
        text = "x = 1  \n# " + ("word " * 40) + "\n"
        rules = [f.rule for f in scan_text("a.py", text)]
        self.assertIn("LONG_COMMENT_LINE", rules)

    def test_docstring_spam_detected_for_function(self):
        body = "\n".join(f"    Detail line {i} of the explanation." for i in range(9))
        text = f'def helper():\n    """Summary.\n\n{body}\n    """\n    return 1\n'
        rules = [f.rule for f in scan_text("a.py", text)]
        self.assertIn("DOCSTRING_SPAM", rules)

    def test_module_docstring_gets_more_room(self):
        body = "\n".join(f"Detail line {i} of the module notes." for i in range(9))
        text = f'"""{body}\n"""\nimport os\n'
        rules = [f.rule for f in scan_text("a.py", text)]
        self.assertNotIn("DOCSTRING_SPAM", rules)

    def test_js_block_comment_detected(self):
        text = "/*\n * Explains the obvious in five lines\n * of generated prose that nobody\n * asked for and nobody will read\n * ever again in the future.\n */\nconst x = 1;\n"
        rules = [f.rule for f in scan_text("a.js", text)]
        self.assertIn("LONG_COMMENT_BLOCK", rules)


class ScrubCommentsTest(unittest.TestCase):
    def test_narration_block_removed_code_kept(self):
        out = scrub_text("a.py", NARRATION)
        self.assertNotIn("This function takes", out)
        self.assertIn("def get_user(user_id):", out)
        self.assertIn("return db.fetch(user_id)", out)

    def test_license_block_kept(self):
        self.assertEqual(scrub_text("a.py", LICENSE_BLOCK), LICENSE_BLOCK)

    def test_wall_after_license_header_removed_header_kept(self):
        header = ("# Copyright 2026 Demo Project\n"
                  "# Licensed under the MIT License. See the\n"
                  "# LICENSE file in the project root for the\n"
                  "# full license text and conditions of use.\n")
        wall = "".join(f"# Generated narration line {i} explaining the obvious.\n"
                       for i in range(6))
        out = scrub_text("a.py", header + wall + "def main():\n    pass\n")
        self.assertIn("# Copyright 2026 Demo Project", out)
        self.assertIn("# full license text and conditions of use.", out)
        self.assertNotIn("Generated narration", out)
        self.assertIn("def main():", out)

    def test_long_license_header_survives(self):
        header = ("# Copyright 2026 Demo Project\n"
                  "# Licensed under the Apache License, Version 2.0 (the License);\n"
                  "# you may not use this file except in compliance with the License.\n"
                  "# You may obtain a copy of the License at the project site.\n"
                  "# Unless required by law, the software is distributed as is,\n"
                  "# without warranty of any kind, and liability is limited.\n"
                  "# See the License for the specific language governing use.\n")
        text = header + "def main():\n    pass\n"
        self.assertEqual(scrub_text("a.py", text), text)

    def test_todo_block_kept(self):
        self.assertEqual(scrub_text("a.py", TODO_BLOCK), TODO_BLOCK)

    def test_short_comment_block_kept(self):
        self.assertEqual(scrub_text("a.py", SHORT_NOTES), SHORT_NOTES)

    def test_js_block_comment_removed(self):
        text = "/*\n * Generated explanation line one\n * line two of the explanation\n * line three of the explanation\n * line four of the explanation\n */\nconst x = 1;\n"
        out = scrub_text("a.js", text)
        self.assertNotIn("Generated explanation", out)
        self.assertIn("const x = 1;", out)

    def test_trailing_comment_untouched(self):
        text = "total = price * qty  # per-order total, tax handled by billing\n"
        self.assertEqual(scrub_text("a.py", text), text)

    def test_docstring_untouched_by_scrub(self):
        body = "\n".join(f"    Detail line {i} of the explanation." for i in range(9))
        text = f'def helper():\n    """Summary.\n\n{body}\n    """\n    return 1\n'
        self.assertEqual(scrub_text("a.py", text), text)

    def test_scrub_is_idempotent(self):
        once = scrub_text("a.py", NARRATION)
        self.assertEqual(scrub_text("a.py", once), once)


if __name__ == "__main__":
    unittest.main(verbosity=2)
