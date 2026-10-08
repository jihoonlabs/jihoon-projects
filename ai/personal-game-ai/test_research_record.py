import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

from game_brief import prepare
from research_record import attach, main


class ResearchRecordTests(unittest.TestCase):
    def setUp(self):
        self.brief = prepare("thumby", {"genre": "리듬", "experience": "타이밍"})
        self.entry = {"category": "hardware", "topic": "오디오 지연", "finding": "실기 측정 필요", "source": "", "checked_on": "2026-10-08", "status": "unknown"}

    def evidence(self):
        return {"device": "thumby", "entries": [copy.deepcopy(self.entry)]}

    def test_unknown_does_not_grant_feasibility_or_approval(self):
        original = copy.deepcopy(self.brief)
        result = attach(self.brief, self.evidence())
        self.assertEqual(result["feasibility"], "not_assessed")
        self.assertFalse(result["specification_approved"])
        self.assertEqual(self.brief, original)
        self.assertEqual(result["research"]["hardware"][0]["status"], "unknown")

    def test_cross_device_rejected(self):
        data = self.evidence()
        data["device"] = "thumby-color"
        with self.assertRaises(ValueError):
            attach(self.brief, data)

    def test_documented_requires_url(self):
        for source in ["", "local.txt", "https://"]:
            data = self.evidence()
            data["entries"][0].update(status="documented", source=source)
            with self.subTest(source=source), self.assertRaises(ValueError):
                attach(self.brief, data)

    def test_measured_keeps_record_reference(self):
        data = self.evidence()
        data["entries"][0].update(status="measured", source="measurements/audio.json")
        result = attach(self.brief, data)
        self.assertEqual(result["research"]["hardware"][0]["source"], "measurements/audio.json")

    def test_bad_entries_rejected(self):
        for change in [{"category": []}, {"checked_on": "2026-02-30"}, {"topic": " "}, {"status": "approved"}]:
            data = self.evidence()
            data["entries"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                attach(self.brief, data)

    def test_approval_and_policy_not_bypassed(self):
        for key, value in [("specification_approved", True), ("policy", {}), ("stage", "completed")]:
            data = copy.deepcopy(self.brief)
            data[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                attach(data, self.evidence())

    def test_cli_preserves_input_and_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            brief, evidence, output = [root / name for name in ["brief.json", "evidence.json", "result.json"]]
            brief.write_text(json.dumps(self.brief))
            evidence.write_text(json.dumps(self.evidence()))
            original = brief.read_bytes()
            args = ["--brief", str(brief), "--evidence", str(evidence), "--output", str(output)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
            saved = output.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(args)
            self.assertEqual(output.read_bytes(), saved)
            self.assertEqual(brief.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
