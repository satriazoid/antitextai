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

    def test_tokenize_keeps_system_and_web_generic_names(self):
        families = _tokenize_family("Arial, Inter, sans-serif")
        self.assertIn("arial", families)
        self.assertIn("inter", families)
        self.assertIn("sans-serif", families)

    def test_system_stack_reports_clean(self):
        findings = scan_text(
            "x", "body { font-family: Arial, Helvetica, sans-serif; }")
        self.assertEqual(findings, [])
        findings = scan_text(
            "x", "code { font-family: Consolas, 'Courier New', monospace; }")
        self.assertEqual(findings, [])

    def test_google_link_to_decorative_face_flags(self):
        html = ('<link href="https://fonts.googleapis.com/css2'
                '?family=Space+Grotesk:wght@400;700" rel="stylesheet">')
        findings = scan_text("x", html)
        self.assertEqual([f.offender for f in findings], ["space grotesk"])

    def test_google_link_to_allowed_face_passes(self):
        html = ('<link href="https://fonts.googleapis.com/css2'
                '?family=Roboto:wght@400;700" rel="stylesheet">')
        self.assertEqual(scan_text("x", html), [])


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
        css = "body { font-family: Inter, sans-serif; }"
        findings = scan_text("test.css", css)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].offender, "inter")
        self.assertEqual(findings[0].recommendation, "Roboto")

    def test_multiple_fonts_one_allowed_one_not(self):
        css = "h1 { font-family: Montserrat, Inter, sans-serif; }"
        findings = scan_text("test.css", css)
        # Montserrat is allowed, Inter is not
        offenders = {f.offender for f in findings}
        self.assertIn("inter", offenders)
        self.assertNotIn("montserrat", offenders)

    def test_generic_keywords_not_flagged(self):
        css = "body { font-family: sans-serif; }"
        findings = scan_text("test.css", css)
        self.assertEqual(findings, [])

    def test_inline_style_detected(self):
        html = '<div style="font-family: Papyrus, serif;">Hello</div>'
        findings = scan_text("test.html", html)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].offender, "papyrus")

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
