"""Portable checks: standard library only, no subprocess/Git/model server."""
import unittest
import request_intake


class PhoneIntakeTests(unittest.TestCase):
    def test_missing_decisions(self):
        result = request_intake.prepare("산길 모험", {"play": "좌우 이동"})
        self.assertEqual([q["id"] for q in result["questions"]], ["finish"])
        self.assertIsNone(result["request"])

    def test_ready_request_preserves_original(self):
        result = request_intake.prepare("산길 모험", {"play": "좌우 이동", "finish": "충돌 종료"})
        self.assertEqual(result["stage"], "request_ready")
        self.assertIn("산길 모험", result["request"]["goal"])
        self.assertEqual(result["request"]["area"], "game")

    def test_model_quotes_and_uncertainty(self):
        brief = "좌우 이동하는 산길 모험"
        extracted = request_intake.extract_settings(brief,
            model=lambda _: '{"play":"좌우 이동","finish":null}')
        self.assertEqual(extracted, {"play": "좌우 이동"})
        self.assertEqual([q["id"] for q in request_intake.prepare(brief, extracted)["questions"]], ["finish"])

    def test_invented_decision_rejected(self):
        with self.assertRaises(ValueError):
            request_intake.extract_settings("산길 모험",
                model=lambda _: '{"play":"격투","finish":null}')

    def test_explicit_settings_skip_model(self):
        def forbidden(_):
            self.fail("model called with complete settings")
        self.assertEqual(request_intake.extract_settings("산길 모험",
            {"play": "이동", "finish": "종료"}, model=forbidden), {})


if __name__ == "__main__":
    unittest.main()
