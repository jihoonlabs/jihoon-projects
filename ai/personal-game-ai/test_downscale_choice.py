import copy
import unittest

from game_brief import prepare
from research_record import attach
from downscale_choice import prepare_choices


class DownscaleChoiceTests(unittest.TestCase):
    def setUp(self):
        brief = prepare("thumby", {"genre": "격투", "experience": "거리 싸움"})
        entries = [{"category": c, "topic": "조사", "finding": "확인 필요", "source": "", "checked_on": "2026-10-08", "status": "unknown"} for c in ["hardware", "gameplay"]]
        self.brief = attach(brief, {"device": "thumby", "entries": entries})
        self.proposal = {"device": "thumby", "options": [{"id": str(i), "title": title, "keep": ["거리 싸움"], "reduce": ["전투원 수"], "unverified": ["실기 속도"]} for i, title in enumerate(["한 화면", "작은 스테이지"])]}

    def test_selection_never_approves_or_claims_feasibility(self):
        result = prepare_choices(self.brief, self.proposal, "0")
        self.assertEqual(result["stage"], "needs_specification")
        self.assertFalse(result["specification_approved"])
        self.assertEqual(result["feasibility"], "not_assessed")
        self.assertNotIn("request", result)

    def test_no_selection_waits_for_user(self):
        result = prepare_choices(self.brief, self.proposal)
        self.assertEqual(result["stage"], "needs_choice")
        self.assertIsNone(result["choices"]["selected"])

    def test_missing_category_rejected(self):
        self.brief["research"]["gameplay"] = []
        with self.assertRaises(ValueError):
            prepare_choices(self.brief, self.proposal)

    def test_wrong_device_duplicate_id_and_bad_selection(self):
        for change in ["device", "duplicate", "selection"]:
            proposal = copy.deepcopy(self.proposal)
            selected = None
            if change == "device":
                proposal["device"] = "thumby-color"
            elif change == "duplicate":
                proposal["options"][1]["id"] = "0"
            else:
                selected = "missing"
            with self.subTest(change=change), self.assertRaises(ValueError):
                prepare_choices(self.brief, proposal, selected)

    def test_loss_and_unknowns_must_be_disclosed(self):
        for key in ["keep", "reduce", "unverified"]:
            proposal = copy.deepcopy(self.proposal)
            proposal["options"][0][key] = []
            with self.subTest(key=key), self.assertRaises(ValueError):
                prepare_choices(self.brief, proposal)

    def test_input_is_preserved(self):
        original = copy.deepcopy(self.brief)
        result = prepare_choices(self.brief, self.proposal)
        result["choices"]["options"][0]["keep"].append("changed")
        self.assertEqual(self.brief, original)
        self.assertEqual(len(self.proposal["options"][0]["keep"]), 1)


if __name__ == "__main__":
    unittest.main()
