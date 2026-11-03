import builtins
import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from recovery_status import get_recovery_summary


class TestRecoveryStatus(unittest.TestCase):
    def test_summary_includes_step_status_and_recovery_availability(self):
        result = get_recovery_summary("execute", "running", True)

        self.assertIn("execute", result["summary"])
        self.assertIn("running", result["summary"])
        self.assertTrue(result["recovery_available"])
        self.assertFalse(
            get_recovery_summary("review_tests", "pending", False)[
                "recovery_available"
            ]
        )

    def test_no_question_when_no_decision_is_required(self):
        result = get_recovery_summary(
            "execute",
            "pending",
            False,
            decision_required=False,
            decision_question="이 문구는 반환되면 안 됩니다.",
        )

        self.assertEqual(result["questions"], [])

    def test_required_decision_returns_only_korean_question(self):
        question = "중단된 작업을 다시 시도할까요?"
        result = get_recovery_summary(
            "execute",
            "waiting_for_user",
            False,
            decision_required=True,
            decision_question=question,
        )

        self.assertEqual(result["questions"], [question])

    def test_required_decision_rejects_missing_or_non_korean_question(self):
        with self.assertRaises(ValueError):
            get_recovery_summary("execute", "pending", False, True)
        with self.assertRaises(ValueError):
            get_recovery_summary(
                "execute", "pending", False, True, "Retry the task?"
            )
        with self.assertRaises(ValueError):
            get_recovery_summary(
                "execute", "pending", False, True, "Retry the task? 네"
            )

    def test_korean_question_may_contain_common_latin_acronyms(self):
        result = get_recovery_summary(
            "execute",
            "waiting_for_user",
            False,
            decision_required=True,
            decision_question="AI 작업을 다시 시도할까요?",
        )

        self.assertEqual(result["questions"], ["AI 작업을 다시 시도할까요?"])

    def test_function_does_not_use_files_or_git_processes(self):
        with (
            patch.object(builtins, "open", side_effect=AssertionError("open")),
            patch.object(Path, "open", side_effect=AssertionError("Path.open")),
            patch.object(Path, "write_text", side_effect=AssertionError("write_text")),
            patch.object(Path, "write_bytes", side_effect=AssertionError("write_bytes")),
            patch.object(subprocess, "run", side_effect=AssertionError("subprocess.run")),
            patch.object(subprocess, "Popen", side_effect=AssertionError("subprocess.Popen")),
            patch.object(os, "system", side_effect=AssertionError("os.system")),
        ):
            result = get_recovery_summary("execute", "running", True)

        self.assertTrue(result["recovery_available"])
        self.assertEqual(result["questions"], [])


if __name__ == "__main__":
    unittest.main()
