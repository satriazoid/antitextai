"""Tests for AI-style prose detection."""
import unittest

from antitextai.styles import StyleFinding, scan_text


class HedgingTest(unittest.TestCase):
    def test_hedge_detected(self):
        findings = scan_text("x.md", "This is generally a good approach.")
        offenders = [f for f in findings if f.rule == "HEDGING"]
        self.assertEqual(len(offenders), 1)
        self.assertEqual(offenders[0].text, "generally")

    def test_no_hedge_no_finding(self):
        findings = scan_text("x.md", "This is a good approach.")
        offenders = [f for f in findings if f.rule == "HEDGING"]
        self.assertEqual(offenders, [])


class TransitionsTest(unittest.TestCase):
    def test_transition_detected(self):
        findings = scan_text("x.md", "Furthermore, this is important.")
        offenders = [f for f in findings if f.rule == "TRANSITION"]
        self.assertEqual(len(offenders), 1)
        self.assertEqual(offenders[0].text, "Furthermore")

    def test_no_transition_no_finding(self):
        findings = scan_text("x.md", "This is important.")
        offenders = [f for f in findings if f.rule == "TRANSITION"]
        self.assertEqual(offenders, [])


class OpenerTest(unittest.TestCase):
    def test_certainly_detected(self):
        findings = scan_text("x.md", "Certainly!\nHere is the code.")
        offenders = [f for f in findings if f.rule == "AI_OPENER"]
        self.assertEqual(len(offenders), 1)

    def test_no_opener_no_finding(self):
        findings = scan_text("x.md", "Here is the code.")
        offenders = [f for f in findings if f.rule == "AI_OPENER"]
        self.assertEqual(offenders, [])


class SignoffTest(unittest.TestCase):
    def test_hope_this_helps_detected(self):
        findings = scan_text("x.md", "Hope this helps!")
        offenders = [f for f in findings if f.rule == "AI_SIGNOFF"]
        self.assertEqual(len(offenders), 1)

    def test_no_signoff_no_finding(self):
        findings = scan_text("x.md", "Here is the code.")
        offenders = [f for f in findings if f.rule == "AI_SIGNOFF"]
        self.assertEqual(offenders, [])


class MidGestureTest(unittest.TestCase):
    def test_important_to_note_detected(self):
        findings = scan_text("x.md", "Caching is essential. It's important to note that TTLs prevent stale data.")
        offenders = [f for f in findings if f.rule == "MID_GESTURE"]
        self.assertEqual(len(offenders), 1)

    def test_no_gesture_no_finding(self):
        findings = scan_text("x.md", "The loop terminates.")
        offenders = [f for f in findings if f.rule == "MID_GESTURE"]
        self.assertEqual(offenders, [])


class BoldKeywordListTest(unittest.TestCase):
    def test_bold_keyword_list_detected(self):
        findings = scan_text("x.md", "- **Security:** This is important.")
        offenders = [f for f in findings if f.rule == "BOLD_KEYWORD_LIST"]
        self.assertEqual(len(offenders), 1)

    def test_no_bold_keyword_no_finding(self):
        findings = scan_text("x.md", "- Security is important.")
        offenders = [f for f in findings if f.rule == "BOLD_KEYWORD_LIST"]
        self.assertEqual(offenders, [])


class EmojiHeadingTest(unittest.TestCase):
    def test_emoji_heading_detected(self):
        findings = scan_text("x.md", "## 🚀 Overview")
        offenders = [f for f in findings if f.rule == "EMOJI_HEADING"]
        self.assertEqual(len(offenders), 1)

    def test_no_emoji_heading_no_finding(self):
        findings = scan_text("x.md", "## Overview")
        offenders = [f for f in findings if f.rule == "EMOJI_HEADING"]
        self.assertEqual(offenders, [])


class FillerSectionTest(unittest.TestCase):
    def test_filler_section_detected(self):
        findings = scan_text("x.md", "## Conclusion")
        offenders = [f for f in findings if f.rule == "FILLER_SECTION"]
        self.assertEqual(len(offenders), 1)

    def test_no_filler_no_finding(self):
        findings = scan_text("x.md", "## Implementation Details")
        offenders = [f for f in findings if f.rule == "FILLER_SECTION"]
        self.assertEqual(offenders, [])


class EmptyTextTest(unittest.TestCase):
    def test_empty_text_no_findings(self):
        self.assertEqual(scan_text("x", ""), [])

    def test_plain_text_no_findings(self):
        findings = scan_text("x", "Plain paragraph.\nNo AI tells here.\n")
        rules = {f.rule for f in findings}
        forbidden = {"AI_OPENER", "AI_SIGNOFF", "HEDGING", "TRANSITION", "MID_GESTURE",
                     "BOLD_KEYWORD_LIST", "EMOJI_HEADING", "FILLER_SECTION"}
        self.assertEqual(rules & forbidden, set())


class FormatReportTest(unittest.TestCase):
    def test_empty_report(self):
        from antitextai.styles import format_report
        out = format_report([])
        self.assertIn("0 file(s)", out)

    def test_findings_are_listed(self):
        from antitextai.styles import format_report
        reports = [
            {
                "path": "a.md",
                "findings": [
                    StyleFinding("a.md", 1, "AI_OPENER", "Certainly!").to_dict(),
                ],
                "count": 1,
                "rules_hit": ["AI_OPENER"],
            }
        ]
        out = format_report(reports)
        self.assertIn("a.md", out)
        self.assertIn("Certainly", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
