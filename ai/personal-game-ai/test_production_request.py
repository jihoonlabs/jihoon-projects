import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import production_request
import production_spec
import test_production_spec


class ProductionRequestTests(unittest.TestCase):
    def setUp(self):
        fixture = test_production_spec.ProductionSpecTests()
        fixture.setUp()
        review = production_spec.build(fixture.brief, fixture.details)
        self.record = production_spec.approve(review, review["digest"])
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "checkout", "-qb", "work/rpg"], check=True)
        (self.root / "docs").mkdir()
        (self.root / "docs/WORK.md").write_text("work")
        (self.root / "AGENTS.md").write_text("rules")
        (self.root / "micropython/Rpg").mkdir(parents=True)
        self.config = self.root / "target.json"
        self.data = {"repository_root": ".", "expected_branch": "work/rpg",
                     "branch_document": "docs/WORK.md", "code_files": [],
                     "max_context_chars": 1000, "generation_profile": "thumby",
                     "edit_directory": "micropython/Rpg"}
        self.config.write_text(json.dumps(self.data))

    def prepare(self, record=None):
        return production_request.prepare(self.record if record is None else record, self.config,
                                          game_directory="micropython/Rpg", expected_branch="work/rpg")

    def test_exact_request_shape_and_no_inherited_engine_approval(self):
        before = copy.deepcopy(self.record)
        result = self.prepare()
        self.assertEqual(set(result["request"]), {"goal", "requirements", "area"})
        self.assertEqual(result["request"]["area"], "game")
        self.assertEqual(result["binding"]["entry_filename"], "Rpg.py")
        self.assertEqual(result["specification_digest"], self.record["digest"])
        self.assertEqual(self.record, before)
        self.assertFalse(list((self.root / "micropython/Rpg").iterdir()))

    def test_tampered_or_missing_approval_is_rejected(self):
        for field in ("stage", "approval", "details", "policy"):
            record = copy.deepcopy(self.record)
            if field == "stage": record["stage"] = "review_specification"
            elif field == "approval": record["approval"] = None
            elif field == "details": record["specification"]["details"]["rules"] = ["changed"]
            else: record["specification"]["brief"]["policy"]["copy_source_game"] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.prepare(record)

    def test_color_does_not_claim_generation_support(self):
        record = copy.deepcopy(self.record)
        record["specification"]["brief"]["device"] = {"id": "thumby-color", "name": "Thumby Color"}
        record["digest"] = production_spec.digest(record["specification"])
        record["approval"]["digest"] = record["digest"]
        with self.assertRaisesRegex(ValueError, "Color"):
            self.prepare(record)

    def test_wrong_target_config_or_actual_branch_blocks(self):
        for key, value in (("edit_directory", "micropython/ThumbyDodge"),
                           ("expected_branch", "other"), ("generation_profile", None)):
            config = {**self.data, key: value}
            self.config.write_text(json.dumps(config))
            with self.subTest(key=key), self.assertRaises(ValueError): self.prepare()
        self.config.write_text(json.dumps(self.data))
        subprocess.run(["git", "-C", str(self.root), "checkout", "-qb", "other"], check=True)
        with self.assertRaisesRegex(RuntimeError, "브랜치"):
            self.prepare()

    def test_existing_game_and_deleted_tracked_file_are_preserved(self):
        game = self.root / "micropython/Rpg/old.py"
        game.write_text("original")
        with self.assertRaises(ValueError): self.prepare()
        self.assertEqual(game.read_text(), "original")
        subprocess.run(["git", "-C", str(self.root), "add", "micropython/Rpg/old.py"], check=True)
        game.unlink()
        with self.assertRaisesRegex(ValueError, "추적"):
            self.prepare()

    def test_symlink_game_and_unsafe_paths_block(self):
        target = self.root / "micropython/Rpg"
        target.rmdir()
        target.symlink_to(self.root / "docs", target_is_directory=True)
        with self.assertRaises(ValueError): self.prepare()
        for path in ("../Rpg", "/tmp/Rpg", "micropython/Rpg/sub", "micropython/not-valid"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                production_request.prepare(self.record, self.config,
                    game_directory=path, expected_branch="work/rpg")

    def test_all_detail_characters_survive_requirement_splitting(self):
        spec = copy.deepcopy(self.record["specification"])
        spec["details"]["rules"] = ["가" * 750, "끝\n정확한 규칙"]
        request = production_request.request_for(spec)
        chunks = [text[len("rules: "):] for text in request["requirements"] if text.startswith("rules: ")]
        self.assertEqual("".join(chunks), "\n".join(spec["details"]["rules"]))
        self.assertTrue(all(len(text) <= 500 for text in request["requirements"]))
        for key in production_request.SECTIONS:
            chunks = [text[len(key + ": "):] for text in request["requirements"] if text.startswith(key + ": ")]
            self.assertEqual("".join(chunks), "\n".join(spec["details"][key]))

    def test_oversize_spec_blocks_without_truncation(self):
        spec = copy.deepcopy(self.record["specification"])
        spec["details"]["rules"] = [str(i) + "x" * 990 for i in range(20)]
        with self.assertRaisesRegex(ValueError, "12개"):
            production_request.request_for(spec)
        spec = copy.deepcopy(self.record["specification"])
        spec["brief"]["choices"]["options"][0]["keep"] = ["x" * 1000 for _ in range(20)]
        with self.assertRaisesRegex(ValueError, "4000자"):
            production_request.request_for(spec)

    def test_cli_saves_request_and_binding_without_overwriting(self):
        record = self.root / "approved.json"
        record.write_text(json.dumps(self.record))
        output = self.root / "bundle"
        args = ["--record", str(record), "--target-config", str(self.config),
                "--game-directory", "micropython/Rpg", "--expected-branch", "work/rpg",
                "--output-dir", str(output)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(production_request.main(args), 0)
        request = (output / "request.json").read_bytes()
        binding = json.loads((output / "binding.json").read_text())
        self.assertEqual(json.loads(request), binding["request"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            production_request.main(args)
        self.assertEqual((output / "request.json").read_bytes(), request)


if __name__ == "__main__":
    unittest.main()
