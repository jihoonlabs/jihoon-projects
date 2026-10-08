import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import request_intake
import workflow_bridge


class BridgeTests(unittest.TestCase):
    def waiting(self, question="조작은?", id="002"):
        return {"stage": "execute", "execution": "waiting_for_user", "details": [{"id": id, "question": question}]}

    def test_dialogue_refreshes_questions_and_stops_at_review_gate(self):
        from unittest.mock import Mock
        ask = Mock(side_effect=["좌우 이동", "충돌 종료"])
        step = Mock(side_effect=[self.waiting("종료 조건은?", "003"), {"stage": "review_tests"}])
        result = workflow_bridge.continue_dialogue("request", "tool", self.waiting(), ask=ask, step=step)
        self.assertEqual(result, {"stage": "review_tests"})
        self.assertEqual(step.call_args_list[0].kwargs, {"answer_id": "002", "answer": "좌우 이동"})
        self.assertEqual(step.call_args_list[1].kwargs, {"answer_id": "003", "answer": "충돌 종료"})
        self.assertEqual(step.call_count, 2)

    def test_dialogue_stop_invalid_answer_and_limit_do_not_submit(self):
        from unittest.mock import Mock
        for answer in (None, "/stop", " ", "x" * 4001):
            step = Mock()
            result = workflow_bridge.continue_dialogue("r", "t", self.waiting(), ask=lambda _: answer, step=step)
            self.assertIn("dialogue_paused", result)
            step.assert_not_called()
        step = Mock(return_value=self.waiting())
        result = workflow_bridge.continue_dialogue("r", "t", self.waiting(), ask=lambda _: "답변", step=step, limit=2)
        self.assertEqual(result["dialogue_paused"], "question_limit")
        self.assertEqual(step.call_count, 2)

    def test_dialogue_never_prompts_at_review_or_error_or_malformed_question(self):
        from unittest.mock import Mock
        ask = Mock(side_effect=AssertionError("unexpected prompt"))
        step = Mock(side_effect=AssertionError("unexpected engine"))
        for result in ({"stage": "review_design"}, {"stage": "review_tests"}, {"stage": "waiting_git"},
                       {"stage": "completed"}, {**self.waiting(), "error": "failed"}):
            self.assertEqual(workflow_bridge.continue_dialogue("r", "t", result, ask=ask, step=step), result)
        result = workflow_bridge.continue_dialogue("r", "t", {**self.waiting(), "details": []}, ask=ask, step=step)
        self.assertIn("error", result)
        ask.assert_not_called()
        step.assert_not_called()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.request = self.root / "request.json"
        self.request.write_text("{}")
        (self.root / "workflow.py").write_text("# fixture")

    def test_delegation_has_no_automatic_approval_and_preserves_request(self):
        response = subprocess.CompletedProcess([], 0, '{"stage":"review_design","sha256":"digest"}', '')
        with patch.object(workflow_bridge.subprocess, "run", return_value=response) as engine:
            result = workflow_bridge.run(self.request, self.root)
        self.assertEqual(result["stage"], "review_design")
        self.assertEqual(result["request_file"], str(self.request))
        self.assertEqual(engine.call_args.args[0], [sys.executable, str(self.root / "workflow.py"), "--request", str(self.request)])
        self.assertEqual(engine.call_args.kwargs["cwd"], self.root)
        self.assertEqual(self.request.read_text(), "{}")

    def test_explicit_review_digest_is_forwarded_without_change(self):
        response = subprocess.CompletedProcess([], 0, '{"stage":"review_tests"}', '')
        with patch.object(workflow_bridge.subprocess, "run", return_value=response) as engine:
            workflow_bridge.run(self.request, self.root, approve="user-digest")
        self.assertEqual(engine.call_args.args[0][-2:], ["--approve-design", "user-digest"])
        with self.assertRaises(ValueError):
            workflow_bridge.run(self.request, self.root, approve="a", confirm="b")

    def test_engine_failure_is_not_reported_as_success(self):
        for stdout in ("", "[]", '{"stage":"completed"}'):
            with self.subTest(stdout=stdout), patch.object(workflow_bridge.subprocess, "run",
                return_value=subprocess.CompletedProcess([], 1, stdout, "branch mismatch")):
                self.assertIn("error", workflow_bridge.run(self.request, self.root))

    def test_intake_saves_and_hands_same_file_to_engine(self):
        target = self.root / "new.json"
        with patch.object(sys, "argv", ["intake", "--interactive", "--workflow-dir", str(self.root),
                "--output", str(target)]), patch.object(sys, "stdin", io.StringIO("산길\n좌우 이동\n충돌 종료\n")), \
                patch.object(sys, "stdout", io.StringIO()) as output, patch.object(sys, "stderr", io.StringIO()), \
                patch.object(workflow_bridge, "run", return_value={"stage": "review_design"}) as bridge:
            self.assertEqual(request_intake.main(), 0)
        self.assertEqual(json.loads(output.getvalue())["stage"], "review_design")
        bridge.assert_called_once_with(target, self.root)
        self.assertEqual(json.loads(target.read_text())["requirements"][0], "핵심 플레이: 좌우 이동")

    def test_missing_engine_blocks_before_subprocess(self):
        with patch.object(workflow_bridge.subprocess, "run") as engine, self.assertRaises(ValueError):
            workflow_bridge.run(self.request, self.root / "missing")
        engine.assert_not_called()

    def test_answer_is_forwarded_as_literal_argument(self):
        answer = '좌우 이동; $(echo nope) "원문"\n둘째 줄'
        with patch.object(workflow_bridge.subprocess, "run", return_value=
                subprocess.CompletedProcess([], 0, '{"stage":"execute"}', '')) as engine:
            workflow_bridge.run(self.request, self.root, answer_id="002", answer=answer)
        self.assertEqual(engine.call_args.args[0][-4:], ["--answer", "002", "--answer-text", answer])
        self.assertNotIn("shell", engine.call_args.kwargs)

    def test_cli_answer_reaches_subprocess_without_shell_expansion(self):
        (self.root / "workflow.py").write_text(
            "import json,sys\nprint(json.dumps({'stage':'waiting_for_user','arguments':sys.argv[1:]}))\n")
        answer = '한글 답변; $(echo nope)\n다음 줄'
        completed = subprocess.run([sys.executable, str(Path(workflow_bridge.__file__).resolve()),
            "--request", str(self.request), "--tool-dir", str(self.root),
            "--answer", "002", "--answer-text", answer],
            capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["arguments"][-4:],
                         ["--answer", "002", "--answer-text", answer])

    def test_interactive_cli_answers_and_returns_review_without_approval(self):
        (self.root / "workflow.py").write_text(
            "import json,sys\n"
            "result = {'stage':'review_design','arguments':sys.argv[1:]} if '--answer' in sys.argv else "
            "{'stage':'execute','execution':'waiting_for_user','details':[{'id':'002','question':'조작은?'}]}\n"
            "print(json.dumps(result))\n", encoding="utf-8")
        completed = subprocess.run([sys.executable, str(Path(workflow_bridge.__file__).resolve()),
            "--request", str(self.request), "--tool-dir", str(self.root), "--interactive"],
            input="좌우 이동\n", capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["stage"], "review_design")
        self.assertEqual(result["arguments"][-4:], ["--answer", "002", "--answer-text", "좌우 이동"])
        self.assertNotIn("--approve-design", result["arguments"])
        self.assertIn("[002] 조작은?", completed.stderr)

    def test_retry_requires_explicit_flag_and_conflicts_block_engine(self):
        with patch.object(workflow_bridge.subprocess, "run", return_value=
                subprocess.CompletedProcess([], 0, '{"stage":"review_design"}', '')) as engine:
            workflow_bridge.run(self.request, self.root, retry=True)
            self.assertEqual(engine.call_args.args[0][-1], "--retry")
            engine.reset_mock()
            for options in ({"retry": True, "approve": "digest"},
                            {"answer_id": "002"}, {"answer": "yes"},
                            {"answer_id": "002", "answer": " "},
                            {"answer_id": "002", "answer": "x" * 4001},
                            {"answer_id": "002", "answer": "yes", "confirm": "digest"}):
                with self.subTest(options=options), self.assertRaises(ValueError):
                    workflow_bridge.run(self.request, self.root, **options)
            engine.assert_not_called()
