import unittest
from unittest.mock import patch

import design_plan
import request_intake


class RequestIntakeTests(unittest.TestCase):
    def test_missing_settings_ask_only_game_decisions(self):
        result = request_intake.prepare("시대극 액션 게임")
        self.assertEqual([q["id"] for q in result["questions"]], ["play", "finish"])
        self.assertIsNone(result["request"])

    def test_supplied_decision_is_not_asked_again(self):
        result = request_intake.prepare("시대극", {"play": "좌우 이동"})
        self.assertEqual([q["id"] for q in result["questions"]], ["finish"])
        self.assertEqual(result["settings"]["play"], "좌우 이동")

    def test_ready_request_preserves_user_text_and_matches_existing_validator(self):
        brief = "시대극 느낌, 평화적인 산길 모험"
        settings = {"play": "좌우 이동으로 피하기", "finish": "충돌하면 종료, 양쪽 버튼 재시작"}
        before = dict(settings)
        result = request_intake.prepare(brief, settings)
        self.assertEqual(result["stage"], "request_ready")
        self.assertIn(brief, result["request"]["goal"])
        self.assertEqual(settings, before)
        self.assertEqual(result["questions"], [])
        self.assertEqual(set(result["request"]), {"goal", "requirements", "area"})
        with patch.object(design_plan, "directory_for", return_value="fixture"):
            self.assertEqual(design_plan.validate_input(**result["request"]), "fixture")

    def test_invalid_and_technical_settings_are_rejected(self):
        for settings in ({"play": ""}, {"finish": "x" * 401}, {"module": "rules.py"}, [], {"play": None}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                request_intake.prepare("game", settings)

    def test_brief_limits(self):
        for brief in ("", " ", "x" * 3001, None):
            with self.subTest(brief=brief), self.assertRaises(ValueError):
                request_intake.prepare(brief)


if __name__ == "__main__":
    unittest.main()
