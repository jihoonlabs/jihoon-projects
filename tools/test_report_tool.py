"""Lightweight regression checks for the standalone report tool."""

from pathlib import Path
import re
import subprocess
import unittest


HTML_PATH = Path(__file__).with_name("index.html")
HTML = HTML_PATH.read_text(encoding="utf-8")


class ReportToolTests(unittest.TestCase):
    def test_remains_a_single_file_with_inline_assets(self):
        self.assertEqual(len(re.findall(r"<style\b", HTML, re.I)), 1)
        self.assertEqual(len(re.findall(r"<script\s*>", HTML, re.I)), 1)
        self.assertNotRegex(HTML, r"(?:src|href)=\"(?:\./|\.\./)(?:css|js)/")

    def test_keeps_excel_and_clipboard_imports(self):
        self.assertIn("XLSX.read", HTML)
        self.assertIn("function handlePaste()", HTML)
        self.assertIn("text.split(/\\r?\\n/)", HTML)
        self.assertIn("function applyParsedData(parsed, nameInfo)", HTML)

    def test_keeps_custom_charts_and_export_controls(self):
        self.assertIn("function addCustomChart()", HTML)
        self.assertIn("function removeCustomChart(id)", HTML)
        self.assertIn("function syncOutputOrder()", HTML)
        self.assertIn("pptx.writeFile", HTML)
        self.assertIn('id="chart-type"', HTML)

    def test_inline_javascript_parses(self):
        scripts = re.findall(r"<script>(.*?)</script>", HTML, re.S | re.I)
        self.assertEqual(len(scripts), 1)
        subprocess.run(
            ["node", "-e", "new Function(process.argv[1])", scripts[0]],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
