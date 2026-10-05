import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import implementation_link as link


class ImplementationLinkTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "outputs"
        self.output.mkdir()
        self.directory = self.root / "sandbox"
        self.directory.mkdir()
        self.folder = self.output / "test_plan_fixture"
        self.folder.mkdir()
        self.path = self.folder / "tests.json"
        self.path.write_text("{}")
        self.code = (
            "import unittest\n"
            "from health import heal\n"
            "class Tests(unittest.TestCase):\n"
            "    def test_heal(self):\n"
            "        self.assertEqual(heal(8, 5, 10), 10)\n"
        )
        self.envelope = {
            "request": {
                "goal": "회복 기능 구현",
                "requirements": {"R1": "최대 체력을 넘지 않는다"},
                "area": "sandbox",
            },
            "design": {"files": [{
                "id": "001",
                "filename": "health.py",
                "functions": [{
                    "name": "heal",
                    "parameters": ["hp", "amount", "maximum"],
                    "behavior": "최대 체력을 넘지 않게 회복한다",
                }],
                "checks": [{
                    "requirement": "R1",
                    "case": "heal(8, 5, 10)",
                    "expected": "10",
                }],
                "depends_on": [],
            }]},
        }
        self.candidate = {"files": [{
            "id": "001",
            "filename": "test_health.py",
            "code": self.code,
            "covers": [{"check": 1, "method": "test_heal"}],
        }]}
        for owner, name, value in (
            (link, "BASE_DIR", self.root),
            (link.edit_loop, "BASE_DIR", self.root),
        ):
            patcher = patch.object(owner, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(
            link.design_plan, "directory_for", return_value=self.directory
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(
            link, "read_confirmed",
            side_effect=lambda *args: (
                copy.deepcopy(self.envelope),
                copy.deepcopy(self.candidate),
                ("snapshot",),
            ),
        )
        self.reader = patcher.start()
        self.addCleanup(patcher.stop)

    def test_install_preserves_exact_code_without_execution(self):
        with patch.object(link, "check_unused"):
            paths = link.install_tests(self.path, "sha")
        self.assertEqual(paths, [self.directory / "test_health.py"])
        self.assertEqual(paths[0].read_text(), self.code)
        self.assertFalse((self.directory / "health.py").exists())
        self.assertFalse((self.root / ".edit_loop.lock").exists())

    def test_existing_file_is_never_overwritten(self):
        destination = self.directory / "test_health.py"
        destination.write_text("existing")
        with patch.object(link, "check_unused"):
            with self.assertRaises(FileExistsError):
                link.install_tests(self.path, "sha")
        self.assertEqual(destination.read_text(), "existing")

    def test_existing_lock_blocks_install(self):
        (self.root / ".edit_loop.lock").write_text("existing")
        with self.assertRaises(RuntimeError):
            link.install_tests(self.path, "sha")
        self.reader.assert_not_called()

    def test_missing_installed_test_blocks_plan(self):
        with self.assertRaises(RuntimeError):
            link.create_plan(self.path, "sha")
        self.assertEqual(list(self.output.glob("plan_*")), [])

    def test_changed_installed_test_blocks_plan(self):
        (self.directory / "test_health.py").write_text("changed")
        with self.assertRaises(RuntimeError):
            link.create_plan(self.path, "sha")

    def test_git_change_blocks_plan(self):
        (self.directory / "test_health.py").write_text(self.code)
        with patch.object(
            link.edit_loop, "check_git_files",
            side_effect=RuntimeError("Git 변경"),
        ):
            with self.assertRaises(RuntimeError):
                link.create_plan(self.path, "sha")

    def test_plan_preserves_contract_without_running_implementation(self):
        (self.directory / "test_health.py").write_text(self.code)
        with patch.object(link.edit_loop, "check_git_files"), patch.object(
            link.plan_tasks, "validate_plan",
            side_effect=lambda proposal, allowed, goal: proposal["tasks"],
        ):
            path = link.create_plan(self.path, "sha")
        tasks = json.loads(path.read_text())
        self.assertEqual(tasks[0]["target"], "sandbox/health.py")
        self.assertEqual(tasks[0]["test_module"], "test_health")
        self.assertEqual(tasks[0]["depends_on"], [])
        self.assertIn("최대 체력을 넘지 않게 회복한다", tasks[0]["prompt"])
        self.assertFalse((self.directory / "health.py").exists())

    def test_generation_profile_prompt_is_included_in_plan(self):
        (self.directory / "test_health.py").write_text(self.code)
        self.envelope["request"]["area"] = "game"
        captured = {}

        def validate(proposal, allowed, goal):
            captured["goal"] = goal
            return proposal["tasks"]

        with patch.object(link.edit_loop, "check_git_files"), patch.object(
            link.plan_tasks, "validate_plan", side_effect=validate
        ), patch.object(
            link.generation_profile,
            "implementation_prompt",
            return_value="PROFILE IMPLEMENTATION",
        ):
            link.create_plan(self.path, "sha")
        self.assertIn("PROFILE IMPLEMENTATION", captured["goal"])

    def test_wrong_digest_is_rejected_before_confirmation_read(self):
        # 실제 읽기 함수로 SHA 검사 경로를 확인한다.
        reader = self.reader.side_effect
        self.reader.side_effect = None
        self.reader.stop = None
        try:
            with patch.object(link, "read_confirmed", self.original_reader):
                with self.assertRaises(RuntimeError):
                    link.read_confirmed(self.path, "wrong")
        finally:
            self.reader.side_effect = reader


# Mock 대신 실제 함수가 필요한 검사에서 사용한다.
ImplementationLinkTests.original_reader = staticmethod(link.read_confirmed)


if __name__ == "__main__":
    unittest.main()