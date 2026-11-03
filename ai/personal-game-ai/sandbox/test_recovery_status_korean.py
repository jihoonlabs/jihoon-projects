import unittest

from recovery_status import get_recovery_summary


class KoreanDecisionQuestionTests(unittest.TestCase):
    def test_english_sentence_with_one_korean_particle_is_rejected(self):
        with self.assertRaises(ValueError):
            get_recovery_summary(
                "execute",
                "pending",
                False,
                decision_required=True,
                decision_question="Retry the task? 네",
            )

    def test_korean_question_with_latin_acronym_is_accepted(self):
        question = "AI 작업을 다시 시도할까요?"
        result = get_recovery_summary(
            "execute",
            "waiting_for_user",
            False,
            decision_required=True,
            decision_question=question,
        )
        self.assertEqual(result["questions"], [question])


if __name__ == "__main__":
    unittest.main()
