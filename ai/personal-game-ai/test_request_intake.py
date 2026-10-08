import json
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock

import design_plan
import request_intake
import workflow


class RequestIntakeTests(unittest.TestCase):
    def test_inferred_settings_require_confirmation_and_failure_falls_back(self):
        cases = (
            ('{"play":"좌우 이동","finish":"충돌 종료, 양쪽 재시작"}', "y\n", "좌우 이동"),
            ('{"play":"좌우 이동","finish":"충돌 종료, 양쪽 재시작"}', "n\n수동 이동\n수동 종료\n", "수동 이동"),
            ('{"play":"invented","finish":null}', "수동 이동\n수동 종료\n", "수동 이동"),
            (OSError("offline"), "수동 이동\n수동 종료\n", "수동 이동"),
        )
        for response, answers, expected in cases:
            with self.subTest(response=response), tempfile.TemporaryDirectory() as folder:
                target = Path(folder) / "request.json"
                model = Mock(side_effect=response) if isinstance(response, Exception) else Mock(return_value=response)
                stderr = io.StringIO()
                with patch.object(sys, "argv", ["request_intake.py", "--interactive", "--infer",
                        "--brief", "좌우 이동. 충돌 종료, 양쪽 재시작", "--output", str(target)]), \
                        patch.object(sys, "stdin", io.StringIO(answers)), \
                        patch.object(sys, "stdout", io.StringIO()), patch.object(sys, "stderr", stderr), \
                        patch("ask_ai.ask_model", model):
                    self.assertEqual(request_intake.main(), 0)
                saved = json.loads(target.read_text())
                self.assertEqual(saved["requirements"][0], "핵심 플레이: " + expected)
                model.assert_called_once()
                if expected == "좌우 이동":
                    self.assertNotIn(request_intake.QUESTIONS["play"], stderr.getvalue())

    def test_extraction_uses_quotes_and_only_missing_settings(self):
        model = Mock(return_value='{"finish":"충돌 종료, 양쪽 재시작"}')
        settings = {"play": "직접 정한 이동"}
        result = request_intake.extract_settings("좌우 피하기. 충돌 종료, 양쪽 재시작", settings, model=model)
        self.assertEqual(result, {"finish": "충돌 종료, 양쪽 재시작"})
        self.assertEqual(settings, {"play": "직접 정한 이동"})
        prompt = model.call_args.args[0]
        self.assertIn('"missing": ["finish"]', prompt)

    def test_complete_settings_skip_model(self):
        model = Mock(side_effect=AssertionError("unexpected model"))
        self.assertEqual(request_intake.extract_settings("game", {"play": "move", "finish": "end"}, model=model), {})
        model.assert_not_called()

    def test_uncertain_extraction_keeps_questions(self):
        extracted = request_intake.extract_settings("시대극", model=lambda _: '{"play":null,"finish":null}')
        self.assertEqual(extracted, {})
        self.assertEqual(len(request_intake.prepare("시대극", extracted)["questions"]), 2)

    def test_invalid_model_proposals_are_rejected(self):
        for response in ('{"play":"invented","finish":null}', '{"play":true,"finish":null}',
                         '{"play":" ","finish":null}', '{"play":null}',
                         '{"play":null,"play":null,"finish":null}',
                         '```json\n{}\n```', '[]', 'x' * 2001, None):
            with self.subTest(response=response), self.assertRaises(ValueError):
                request_intake.extract_settings("시대극", model=lambda _: response)

    def cli(self, *args, input=None):
        return subprocess.run(
            [sys.executable, str(Path(request_intake.__file__).resolve()), *args],
            capture_output=True, text=True, encoding="utf-8", check=False,
            timeout=10,
            input=input,
        )

    def test_interactive_collects_missing_answers_and_saves_request(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "request.json"
            result = self.cli("--interactive", "--play", "좌우 피하기", "--output", str(target),
                              input="산길 모험\n충돌 종료\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["stage"], "request_ready")
            self.assertNotIn(request_intake.QUESTIONS["play"], result.stderr)
            self.assertIn(request_intake.QUESTIONS["finish"], result.stderr)
            self.assertEqual(json.loads(target.read_text()), payload["request"])

    def test_interactive_default_creates_distinct_requests_next_to_tool(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / "request_intake.py"
            script.write_bytes(Path(request_intake.__file__).read_bytes())
            for _ in range(2):
                result = subprocess.run([sys.executable, str(script), "--interactive"],
                    input="모험\n좌우 이동\n충돌 종료\n", capture_output=True,
                    text=True, encoding="utf-8", timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
            files = list((Path(folder) / "outputs").glob("request_*.json"))
            self.assertEqual(len(files), 2)
            self.assertEqual(json.loads(files[0].read_text()), json.loads(files[1].read_text()))

    def test_output_preserves_existing_file_and_rejects_incomplete_input(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "request.json"
            target.write_bytes(b"existing")
            result = self.cli("--brief", "game", "--play", "move", "--finish", "end", "--output", str(target))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(target.read_bytes(), b"existing")
            target.unlink()
            for args, answer in ((["--brief", "game"], None),
                                 (["--interactive", "--brief", "game"], "move\n"),
                                 (["--interactive", "--brief", "game"], " \n")):
                result = self.cli(*args, "--output", str(target), input=answer)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse(target.exists())

    def test_cli_unicode_and_partial_settings(self):
        result = self.cli("--brief", "시대극 산길 모험", "--play", "좌우 이동")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["brief"], "시대극 산길 모험")
        self.assertEqual(payload["settings"], {"play": "좌우 이동"})
        self.assertEqual([q["id"] for q in payload["questions"]], ["finish"])

    def test_cli_request_only_matches_prepare(self):
        result = self.cli("--brief", "산길", "--play", "피하기", "--finish", "충돌 종료", "--request-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), request_intake.prepare(
            "산길", {"play": "피하기", "finish": "충돌 종료"})["request"])

    def test_cli_invalid_inputs_do_not_emit_request(self):
        cases = (
            (), ("--brief", ""), ("--brief", "x" * 3001),
            ("--brief", "game", "--play", " "),
            ("--brief", "game", "--finish", "x" * 401),
            ("--brief", "game", "--request-only"),
            ("--brief", "game", "--play", "move", "--request-only"),
            ("--brief", "game", "--unknown"),
        )
        for args in cases:
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("error:", result.stderr)

    def test_cli_request_file_is_accepted_without_modification_or_model_call(self):
        # Exercise the real loader and validator; only game-directory selection
        # is replaced because this Child retains the parent's target config.
        brief = "🌸" * 3000
        settings = {"play": "좌" * 400, "finish": "끝" * 400}
        result = self.cli("--brief", brief, "--play", settings["play"],
                          "--finish", settings["finish"], "--request-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        raw = result.stdout.encode("utf-8")
        self.assertLessEqual(len(raw), 20000)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "new-request.json"
            path.write_bytes(raw)
            with patch.object(design_plan, "directory_for", return_value=Path(folder)), \
                    patch.object(workflow.edit_loop, "ask_model", side_effect=AssertionError("unexpected model call")):
                loaded_path, loaded_bytes, loaded = workflow.load_request(path)
            self.assertEqual(loaded_path, path)
            self.assertEqual(loaded_bytes, raw)
            self.assertEqual(loaded, request_intake.prepare(brief, settings)["request"])
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_intake_status_output_cannot_be_used_as_workflow_request(self):
        result = self.cli("--brief", "회피 게임")
        self.assertEqual(result.returncode, 0, result.stderr)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "incomplete.json"
            path.write_text(result.stdout, encoding="utf-8")
            with patch.object(design_plan, "directory_for") as directory, \
                    self.assertRaises(ValueError):
                workflow.load_request(path)
            directory.assert_not_called()

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
