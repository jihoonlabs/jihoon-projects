import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import test_downscale_choice
from downscale_choice import prepare_choices
from production_spec import build, approve, digest, main


class ProductionSpecTests(unittest.TestCase):
    def setUp(self):
        fixture = test_downscale_choice.DownscaleChoiceTests()
        fixture.setUp()
        self.brief = prepare_choices(fixture.brief, fixture.proposal, "0")
        self.details = {k: ["検証前の候補"] for k in ["scope", "rules", "controls", "display_defaults", "resource_budget", "acceptance", "unverified"]}

    def test_review_is_not_approval(self):
        result = build(self.brief, self.details)
        self.assertEqual(result["stage"], "review_specification")
        self.assertIsNone(result["approval"])

    def test_explicit_digest_approval(self):
        result = build(self.brief, self.details)
        approved = approve(result, result["digest"])
        self.assertEqual(approved["stage"], "specification_approved")
        self.assertEqual(approved["approval"]["digest"], result["digest"])
        self.assertIsNone(result["approval"])
        self.assertNotIn("request", approved)

    def test_modifications_invalidate_old_digest(self):
        for section in ["details", "brief"]:
            result = build(self.brief, self.details)
            old = result["digest"]
            if section == "details":
                result["specification"]["details"]["controls"] = ["別の操作"]
            else:
                result["specification"]["brief"]["settings"]["genre"] = "探索"
            with self.subTest(section=section), self.assertRaises(ValueError):
                approve(result, old)

    def test_invalid_policy_rejected_even_with_new_digest(self):
        result = build(self.brief, self.details)
        result["specification"]["brief"]["policy"]["copy_source_game"] = True
        result["digest"] = digest(result["specification"])
        with self.assertRaises(ValueError):
            approve(result, result["digest"])

    def test_missing_details_and_unselected_brief_rejected(self):
        details = copy.deepcopy(self.details)
        del details["acceptance"]
        with self.assertRaises(ValueError):
            build(self.brief, details)
        self.brief["choices"]["selected"] = None
        with self.assertRaises(ValueError):
            build(self.brief, self.details)

    def test_cli_two_separate_steps(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p / "brief.json").write_text(json.dumps(self.brief))
            (p / "details.json").write_text(json.dumps(self.details))
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--brief", str(p / "brief.json"), "--details", str(p / "details.json"), "--output", str(p / "review.json")])
                record = json.loads((p / "review.json").read_text())
                main(["--record", str(p / "review.json"), "--approve", record["digest"], "--output", str(p / "approved.json")])
            self.assertEqual(json.loads((p / "approved.json").read_text())["stage"], "specification_approved")
            self.assertIsNone(json.loads((p / "review.json").read_text())["approval"])


if __name__ == "__main__":
    unittest.main()
