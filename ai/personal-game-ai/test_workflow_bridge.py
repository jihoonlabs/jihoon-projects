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
