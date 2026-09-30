"""Tests for font-family detection."""
import pathlib
import tempfile
import unittest

from antitextai.fonts import ALLOWED, FontFinding, _recommend, _tokenize_family, scan_text


class TokenizeTest(unittest.TestCase):
    def test_splits_on_comma(self):
        self.assertEqual(_tokenize_family("Roboto, sans-serif"), ["roboto", "sans-serif"])

    def test_strips_quotes(self):
        self.assertEqual(_tokenize_family("'Open Sans', Helvetica"), ["open sans", "helvetica"])

    def test_filters_guards(self):
        families = _tokenize_family("Arial, sans-serif, serif")
        self.assertIn("arial", families)
        self.assertIn("sans-serif", families)
        self.assertIn("serif", families)


class RecommendTest(unittest.TestCase):
    def test_unknown_gets_roboto_by_default(self):
        self.assertEqual(_recommend("Comic Sans"), "Roboto")

    def test_humanist_gets_open_sans(self):
        self.assertEqual(_recommend("humanist"), "Open Sans")

    def test_geometric_gets_montserrat(self):
        self.assertEqual(_recommend("Impact"), "Montserrat")


class ScanTextTest(unittest.TestCase):
    def test_allowed_fonts_not_flagged(self):
        css = "body { font-family: Roboto, sans-serif; }"
        findings = scan_text("test.css", css)
        self.assertEqual(findings, [])

    def test_disallowed_font_flagged(self):
        css = "body { font-family: Arial, sans-serif; }"
        findings = scan_text("test.css", css)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].offender, "arial")
        self.assertEqual(findings[0].recommendation, "Roboto")

    def test_multiple_fonts_one_allowed_one_not(self):
        css = "h1 { font-family: Montserrat, Arial, sans-serif; }"
        findings = scan_text("test.css", css)
        # Montserrat is allowed, Arial is not
        offenders = {f.offender for f in findings}
        self.assertIn("arial", offenders)
        self.assertNotIn("montserrat", offenders)

    def test_generic_keywords_not_flagged(self):
        css = "body { font-family: sans-serif; }"
        findings = scan_text("test.css", css)
        self.assertEqual(findings, [])

    def test_inline_style_detected(self):
        html = '<div style="font-family: Times New Roman, serif;">Hello</div>'
        findings = scan_text("test.html", html)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].offender, "times new roman")

    def test_google_fonts_link_detected(self):
        html = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700" rel="stylesheet">'
        findings = scan_text("test.html", html)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].offender, "inter")

    def test_all_allowed_fonts_pass(self):
        all_allowed = ", ".join(sorted(ALLOWED))
        css = f"body {{ font-family: {all_allowed}; }}"
        findings = scan_text("test.css", css)
        self.assertEqual(findings, [])

    def test_empty_text_no_findings(self):
        self.assertEqual(scan_text("x", ""), [])

    def test_no_font_declaration_no_findings(self):
        self.assertEqual(scan_text("x", "body { color: red; }"), [])


class FormatReportTest(unittest.TestCase):
    def test_empty_report(self):
        from antitextai.fonts import format_report
        out = format_report([])
        self.assertIn("0 file(s)", out)

    def test_findings_are_listed(self):
        from antitextai.fonts import format_report
        reports = [
            {
                "path": "a.css",
                "findings": [
                    FontFinding("a.css", 1, 10, "Arial, sans-serif", "arial", "Roboto").to_dict(),
                ],
                "count": 1,
            }
        ]
        out = format_report(reports)
        self.assertIn("a.css", out)
        self.assertIn("Arial", out)
        self.assertIn("Roboto", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
