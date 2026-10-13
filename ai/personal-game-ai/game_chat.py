"""Natural-language entry point for the configured monochrome Thumby game."""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import uuid

import ask_ai
import edit_loop
import generation_profile
from read_context import git_output, read_context

BASE_DIR = Path(__file__).resolve().parent
GOAL = "로컬 Ollama로 실제 플레이 가능한 일반 Thumby 게임을 만든다."
FIXED_TEST = "test_floor_movement"


def validate_action(value, allowed):
    if not isinstance(value, dict):
        raise ValueError("작업은 JSON 객체여야 합니다.")
    action = value.get("action")
    fields = {
        "status": {"action"}, "test": {"action"},
        "read": {"action", "target"},
        "edit": {"action", "target", "instruction"},
        "question": {"action", "question"},
    }
    if not isinstance(action, str) or action not in fields or set(value) != fields[action]:
        raise ValueError("허용된 단일 작업과 정확한 필드만 사용할 수 있습니다.")
    if action in ("read", "edit") and value["target"] not in allowed:
        raise ValueError("현재 게임의 실행 파일만 읽거나 수정할 수 있습니다.")
    for key in ("instruction", "question"):
        if key in value and (not isinstance(value[key], str) or not value[key].strip()
                             or len(value[key]) > 2000):
            raise ValueError(key + "는 1~2000자여야 합니다.")
    return value


def docker_ready():
    # Do not generate a candidate when its isolated checker cannot run.
    result = subprocess.run(["docker", "image", "inspect", "python:3.11-slim"],
                            capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise RuntimeError("Docker 실행과 python:3.11-slim 이미지 준비가 필요합니다.")


class GameChat:
    def __init__(self, base=None, model=None):
        self.base = BASE_DIR if base is None else Path(base).resolve()
        self.config_path = self.base / "target.json"
        self.model = ask_ai.ask_model if model is None else model
        self.history = []
        self.pending = None
        self.folder = None

    def location(self):
        context = read_context(self.config_path)
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        directory, root = edit_loop.game_location()
        edit_loop.check_directory(directory)
        if config.get("generation_profile") != "thumby" or directory.name != "ThumbyGrowth":
            raise ValueError("첫 대화 실행기는 현재 ThumbyGrowth 게임만 지원합니다.")
        allowed = ("rules.py", "ThumbyGrowth.py")
        for name in (*allowed, FIXED_TEST + ".py"):
            path = directory / name
            if path.is_symlink() or not path.is_file():
                raise ValueError("일반 게임 파일과 고정 테스트가 필요합니다: " + name)
        return directory, root, context, allowed

    def record(self, value):
        if self.folder is None:
            self.folder = self.base / "outputs" / ("chat_" + uuid.uuid4().hex)
            self.folder.mkdir(parents=True)
        with (self.folder / "turns.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False) + "\n")

    def route(self, text, directory, context, allowed):
        shortcuts = {"/status": "status", "/test": "test"}
        if text in shortcuts:
            return {"action": shortcuts[text]}
        if text.startswith("/read "):
            return validate_action({"action": "read", "target": text[6:].strip()}, allowed)
        summaries = {}
        for name in allowed:
            tree = ast.parse((directory / name).read_text(encoding="utf-8"))
            summaries[name] = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        prompt = (
            "최상위 목적: " + GOAL + "\n"
            "사용자 지시를 실행 가능한 단일 작업으로 해석하세요. 실제 실행 결과를 주장하지 마세요.\n"
            "상태 확인=status, 현재 고정 검사=test, 코드 확인=read, 명시적 코드 수정=edit.\n"
            "코드 확인이나 설명 요청을 edit로 바꾸지 마세요. 모호하거나 여러 파일 수정이 필요하면 question.\n"
            "게임 새로 생성, 테스트 변경, Git/폴더/셸 작업, 외부 API는 아직 지원하지 않습니다.\n"
            "수정 지시는 사용자 의도를 보존하고 새 수치/기능을 임의로 정하지 마세요.\n"
            "Markdown 없이 다음 형식 중 JSON 객체 하나만 반환하세요:\n"
            '{"action":"status"} 또는 {"action":"test"}\n'
            '{"action":"read","target":"rules.py"}\n'
            '{"action":"edit","target":"rules.py","instruction":"수정 요청"}\n'
            '{"action":"question","question":"한국어 질문 또는 지원 범위 설명"}\n'
            "허용 파일/함수: " + json.dumps(summaries, ensure_ascii=False) + "\n"
            "작업 문맥:\n" + context + "\n"
            "최근 대화와 실제 결과:\n" + json.dumps(self.history[-4:], ensure_ascii=False) + "\n"
            "현재 사용자 지시:\n" + text
        )
        raw = self.model(prompt)
        if not isinstance(raw, str) or len(raw) > 16000:
            raise ValueError("모델 작업 응답의 길이 또는 형식이 잘못됐습니다.")
        self.record({"router_response": raw})
        return validate_action(json.loads(raw), allowed)

    def edit(self, action, directory):
        target_file = "game/" + action["target"]
        request = (GOAL + "\n" + action["instruction"]
                   + "\n다른 파일, 함수 계약, 저장 형식, 고정 테스트를 변경하지 마세요.\n"
                     "현재 일반 Thumby API와 MicroPython/CPython 실행 구분을 유지하세요.")
        target, test = edit_loop.prepare_edit(target_file, request, FIXED_TEST)
        original, fixed = target.read_bytes(), test.read_bytes()
        candidates = set()

        def generate(prompt):
            raw = self.model(prompt)
            proposal = json.loads(raw)
            if isinstance(proposal, dict) and proposal.get("action") == "edit":
                code = proposal.get("code")
                if isinstance(code, str):
                    generation_profile.validate_code("game", code, action["target"])
                    candidates.add((code.rstrip() + "\n").encode("utf-8"))
            return raw

        def restore():
            # Restore only this turn's candidate, never an unrelated external edit.
            if target.read_bytes() != original:
                if target.read_bytes() not in candidates or test.read_bytes() != fixed:
                    raise RuntimeError("외부 변경을 발견해 복원을 중단했습니다. 실행 기록을 확인하세요.")
                target.write_bytes(original)

        docker_ready()
        try:
            passed, feedback = edit_loop.run_test(self.folder / "baseline.txt", FIXED_TEST,
                                                  work_dir=directory)
            if not passed:
                return {"status": "blocked", "message": "수정 전 고정 검사부터 실패했습니다.",
                        "test_log": str(self.folder / "baseline.txt"), "feedback": feedback[-2000:]}
            # A Docker baseline can take time; recheck state before generation starts.
            if target.read_bytes() != original or test.read_bytes() != fixed:
                raise RuntimeError("수정 전 검사 중 파일이 변경됐습니다.")
            result = edit_loop.run_edit(target_file, request, FIXED_TEST, model=generate)
            if result["status"] != "tests_passed":
                restore()
            if result["status"] == "waiting_for_user":
                self.pending = {**action, "question": result["question"]}
            return {**result, "target": action["target"], "test_module": FIXED_TEST,
                    "message": ("수정과 고정 검사 통과. Git 검토·커밋과 실기 확인이 남았습니다."
                                if result["status"] == "tests_passed" else
                                "수정을 완료하지 못했습니다. 이번 후보는 원본으로 복원했습니다.")}
        except Exception:
            restore()
            raise

    def turn(self, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValueError("지시는 1~2000자여야 합니다.")
        text = text.strip()
        directory, root, context, allowed = self.location()
        lock = self.base / ".game_chat.lock"
        try:
            with lock.open("x"):
                pass
        except FileExistsError:
            raise RuntimeError("다른 대화 작업이 실행 중이거나 이전 실행이 중단됐습니다.") from None
        try:
            self.record({"user": text, "goal": GOAL})
            if text == "/cancel":
                self.pending = None
                result = {"status": "cancelled", "message": "대기 중인 수정 요청을 취소했습니다."}
                action = {"action": "cancel"}
            else:
                if self.pending is not None and not text.startswith("/"):
                    previous = self.pending
                    instruction = previous["instruction"] + "\n질문: " + previous["question"] + "\n사용자 답변: " + text
                    action = validate_action({"action": "edit", "target": previous["target"],
                                              "instruction": instruction}, allowed)
                    self.pending = None
                else:
                    action = self.route(text, directory, context, allowed)
                # Never execute a model plan under a changed branch/context.
                if read_context(self.config_path) != context:
                    raise RuntimeError("지시 해석 중 작업 문맥이 변경됐습니다.")
                if action["action"] == "status":
                    result = {"status": "inspected", "goal": GOAL,
                              "branch": git_output(root, "branch", "--show-current"),
                              "game_directory": str(directory),
                              "git_changes": git_output(root, "status", "--short", "--", str(directory)),
                              "supported": ["status", "read", "test", "edit"],
                              "model": ask_ai.payload["model"],
                              "model_options": ask_ai.model_options(),
                              "fixed_test": FIXED_TEST,
                              "message": "현재 파일 상태입니다. 테스트와 실기 플레이는 실행하지 않았습니다."}
                elif action["action"] == "read":
                    result = {"status": "read", "target": action["target"],
                              "code": (directory / action["target"]).read_text(encoding="utf-8")}
                elif action["action"] == "test":
                    docker_ready()
                    passed, feedback = edit_loop.run_test(self.folder / "test.txt", FIXED_TEST,
                                                          work_dir=directory)
                    result = {"status": "tests_passed" if passed else "failed",
                              "test_module": FIXED_TEST, "test_log": str(self.folder / "test.txt"),
                              "feedback": feedback[-2000:],
                              "message": "고정 검사 결과입니다. 전체 게임 검사·기기 플레이 결과는 아닙니다."}
                elif action["action"] == "question":
                    result = {"status": "waiting_for_user", "question": action["question"]}
                else:
                    result = self.edit(action, directory)
            self.record({"action": action, "result": result})
            self.history.append({"user": text[:500], "action": action["action"],
                                 "status": result["status"],
                                 "message": result.get("question", result.get("message", ""))[:500]})
            self.history = self.history[-4:]
            return result
        except Exception as error:
            self.record({"result": {"status": "blocked", "error": str(error)}})
            raise
        finally:
            lock.unlink()


def show(result):
    if "code" in result:
        print(result["code"])
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Ollama와 대화하며 현재 Thumby 게임 작업 실행")
    parser.add_argument("--once", help="지시 하나를 실행하고 종료")
    args = parser.parse_args()
    chat = GameChat()
    print("목표: " + GOAL)
    print("상태·코드 확인·고정 검사·단일 파일 수정 | /status /test /read rules.py /cancel /exit")
    while True:
        try:
            text = args.once if args.once is not None else input("나> ")
            if text.strip() == "/exit":
                return 0
            print("작업 중...", flush=True)
            result = chat.turn(text)
            show(result)
        except (EOFError, KeyboardInterrupt):
            print("\n대화를 종료합니다.")
            return 0
        except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
            result = {"status": "blocked", "error": str(error)}
            print("중단: " + str(error))
        if args.once is not None:
            return 1 if result["status"] in ("blocked", "failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
