"""Tests for .docx text extraction and scanning."""
import io
import unittest
import zipfile

from antitextai.word import extract_text, scan_data

DOCUMENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Certainly! The report is ready.</w:t></w:r></w:p>
    <w:p><w:r><w:t>Sales use </w:t></w:r><w:r><w:t>\u201csmart quotes\u201d here.</w:t></w:r></w:p>
  </w:body>
</w:document>
"""


def make_docx(xml: str = DOCUMENT_XML) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


class ExtractTextTest(unittest.TestCase):
    def test_paragraphs_joined_in_order(self):
        text = extract_text(make_docx())
        self.assertEqual(
            text,
            "Certainly! The report is ready.\nSales use \u201csmart quotes\u201d here.",
        )

    def test_not_a_zip_returns_none(self):
        self.assertIsNone(extract_text(b"not a docx at all"))

    def test_zip_without_document_xml_returns_none(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("other.txt", "hello")
        self.assertIsNone(extract_text(buf.getvalue()))


class ScanWordTest(unittest.TestCase):
    def test_frame_and_smart_quotes_reported(self):
        report = scan_data("report.docx", make_docx())
        self.assertIsNotNone(report)
        self.assertGreater(report["count"], 0)
        rules = {f["rule"] for f in report["findings"]}
        self.assertTrue(any(r.startswith("U+201") for r in rules))

    def test_clean_document_reports_nothing(self):
        xml = DOCUMENT_XML.replace("Certainly! The report is ready.", "The report is ready.")
        xml = xml.replace("\u201csmart quotes\u201d", '"smart quotes"')
        report = scan_data("clean.docx", make_docx(xml))
        self.assertEqual(report["count"], 0)

    def test_unreadable_data_returns_none(self):
        self.assertIsNone(scan_data("broken.docx", b"junk"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

SPACED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:jc w:val="distribute"/></w:pPr><w:r><w:rPr><w:spacing w:val="40"/></w:rPr><w:t>Sales\u00a0grew\u2009fast.</w:t></w:r></w:p>
  </w:body>
</w:document>
"""

JUSTIFIED_PLAIN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:jc w:val="both"/><w:spacing w:after="120"/></w:pPr><w:r><w:t>Plain justified text.</w:t></w:r></w:p>
  </w:body>
</w:document>
"""


class WordSpacingTest(unittest.TestCase):
    def test_wide_spacing_findings(self):
        report = scan_data("spaced.docx", make_docx(SPACED_XML))
        rules = {f["rule"] for f in report["findings"]}
        self.assertIn("WIDE_SPACES", rules)
        self.assertIn("WORD_JUSTIFY", rules)
        self.assertIn("WORD_CHAR_SPACING", rules)

    def test_justify_alone_is_not_flagged(self):
        report = scan_data("plain.docx", make_docx(JUSTIFIED_PLAIN_XML))
        rules = {f["rule"] for f in report["findings"]}
        self.assertNotIn("WORD_JUSTIFY", rules)
        self.assertNotIn("WORD_CHAR_SPACING", rules)
