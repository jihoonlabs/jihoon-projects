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
