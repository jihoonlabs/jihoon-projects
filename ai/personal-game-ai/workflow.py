import argparse
import contextlib
import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any, TypedDict


class DesignAttemptDiagnostic(TypedDict):
    file: str
    status: Any
    error: Any


class DesignDiagnostic(TypedDict):
    folder: str
    attempts: list[DesignAttemptDiagnostic]

import design_plan
import edit_loop
import execute_plan
import implementation_link
import test_plan

BASE_DIR = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_state(path, state):
    temporary = path.with_name("state_" + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.is_symlink():
            raise RuntimeError("상태 파일이 심볼릭 링크로 변경됐습니다.")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def protect(state, paths):
    for path in paths:
        path = Path(path).absolute()
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("보호할 산출물이 일반 파일이 아닙니다.")
        relative = path.relative_to(BASE_DIR).as_posix()
        state["protected"][relative] = digest(path.read_bytes())


def check_protected(state):
    verify_plan(state)
    for relative, expected in state["protected"].items():
        path = BASE_DIR / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise RuntimeError("보호 산출물 경로가 잘못됐습니다.")
        current = BASE_DIR
        for part in Path(relative).parts:
            current = current / part
            if current.is_symlink():
                raise RuntimeError("보호 산출물 경로에 심볼릭 링크가 있습니다.")
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise RuntimeError("산출물이 변경됐습니다: " + relative)



def plan_contract(path):
    path = execute_plan.resolve_plan(path)
    tasks = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(tasks, list) or not tasks:
        raise RuntimeError("계획 계약 기록이 잘못됐습니다.")
    return [
        {
            key: task.get(key, [] if key == "depends_on" else None)
            for key in (
                "id", "kind", "target", "test_module", "prompt", "depends_on"
            )
        }
        for task in tasks
    ]


def verify_plan(state):
    if "plan" in state:
        current = plan_contract(BASE_DIR / state["plan"])
        if current != state.get("plan_contract"):
            raise RuntimeError("실행 계획의 작업 계약이 변경됐습니다.")

def load_request(path):
    path = Path(path).absolute()
    if path.is_symlink() or not path.is_file():
        raise ValueError("일반 요청 파일이 필요합니다.")
    data = path.read_bytes()
    if len(data) > 20000:
        raise ValueError("요청 파일은 20000바이트 이내여야 합니다.")
    request = json.loads(data)
    if not isinstance(request, dict) or set(request) != {
        "goal", "requirements", "area"
    }:
        raise ValueError("요청에는 goal·requirements·area만 필요합니다.")
    design_plan.validate_input(
        request["goal"], request["requirements"], request["area"]
    )
    return path, data, request


def installed_tests(state):
    files = state["installed"]
    directory = design_plan.directory_for(state["request"]["area"])
    missing_git = []
    for relative, expected in files.items():
        path = Path(os.path.abspath(BASE_DIR / relative))
        if (
            path.is_symlink()
            or path.parent != directory
            or not path.is_file()
            or digest(path.read_bytes()) != expected
        ):
            raise RuntimeError("설치 테스트가 변경됐습니다: " + relative)
        root = Path(edit_loop.git_output(
            path.parent, "rev-parse", "--show-toplevel"
        )).resolve()
        name = path.relative_to(root).as_posix()
        tracked = edit_loop.git_output(root, "ls-files", "--", name)
        status = edit_loop.git_output(
            root, "status", "--porcelain=v1",
            "--untracked-files=all", "--", name,
        )
        if not tracked or status:
            missing_git.append(name)
    return missing_git


def plan_status(path):
    path = execute_plan.resolve_plan(path)
    tasks = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(tasks, list) or not tasks:
        raise RuntimeError("실행 계획 기록이 잘못됐습니다.")
    if all(task.get("status") == "tests_passed" for task in tasks):
        return "completed", []
    blocked = [
        task for task in tasks
        if task.get("status") in ("failed", "running")
    ]
    if blocked:
        return "blocked", [
            {
                "id": task["id"],
                "status": task["status"],
                "error": task.get("error", "이전 실행 중단 상태 확인 필요"),
            }
            for task in blocked
        ]
    waiting = [
        {"id": task["id"], "question": task["question"]}
        for task in tasks if task.get("status") == "waiting_for_user"
    ]
    return ("waiting_for_user", waiting) if waiting else ("ready", [])



def generate_candidate(state, model):
    feedback = state.get("test_feedback")
    if feedback is None:
        return test_plan.generate_tests(BASE_DIR / state["design"], model=model)
    previous = json.loads(
        (BASE_DIR / state["previous_tests"]).read_text(encoding="utf-8")
    )["tests"]
    def revised_model(prompt):
        return model(
            prompt
            + "\n\n# 이전 테스트 후보\n"
            + json.dumps(previous, ensure_ascii=False)
            + "\n# 검토 피드백\n" + feedback
            + "\n기존 설계 계약을 유지하고 전체 후보를 다시 반환하세요."
        )
    return test_plan.generate_tests(
        BASE_DIR / state["design"], model=revised_model
    )


def connect_reviewed_design(state, state_path, path):
    if state["stage"] != "review_design":
        raise ValueError("설계 검토 단계에서만 수정 설계를 연결할 수 있습니다.")
    source, data, envelope = design_plan.read_design(path)
    expected_request = {
        "goal": state["request"]["goal"],
        "requirements": {
            f"R{number}": value
            for number, value in enumerate(state["request"]["requirements"], 1)
        },
        "area": state["request"]["area"],
    }
    revision = envelope.get("revision", {})
    if (
        envelope["request"] != expected_request
        or envelope["context"] != state["context"]
        or revision.get("source") != state["design"]
        or revision.get("source_sha256") != state["design_sha256"]
    ):
        raise RuntimeError("현재 설계의 목표·문맥·수정 이력과 다릅니다.")
    approval = source.with_name("approval.json")
    if approval.exists() or approval.is_symlink():
        raise ValueError("아직 승인하지 않은 수정 설계만 연결할 수 있습니다.")
    check_protected(state)
    if source.read_bytes() != data:
        raise RuntimeError("연결 중 수정 설계가 변경됐습니다.")
    history = state_path.parent / ("design_before_" + uuid.uuid4().hex + ".json")
    with history.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    state["previous_design"] = state["design"]
    state["design"] = str(source.relative_to(BASE_DIR))
    state["design_sha256"] = digest(data)
    protect(state, [source])
    write_state(state_path, state)

def advance(state, state_path, model, approve, confirm, answer_id, answer, feedback=None):
    def save():
        write_state(state_path, state)

    stage = state["stage"]
    if feedback is not None and stage != "review_tests":
        raise ValueError("테스트 검토 단계에서만 피드백할 수 있습니다.")
    if approve is not None and stage != "review_design":
        raise ValueError("설계 검토 단계에서만 설계를 승인할 수 있습니다.")
    if confirm is not None and stage != "review_tests":
        raise ValueError("테스트 검토 단계에서만 후보를 확정할 수 있습니다.")
    if (answer_id is not None or answer is not None) and stage != "execute":
        raise ValueError("실행 질문 단계에서만 답변할 수 있습니다.")
    if (answer_id is None) != (answer is None):
        raise ValueError("작업 ID와 답변을 함께 지정하세요.")

    if stage == "new":
        # 호출 전 상태를 저장해 강제 종료 뒤 중복 모델 호출을 막는다.
        state["stage"] = "generating_design"
        save()
        path = design_plan.generate_design(
            state["request"]["goal"],
            state["request"]["requirements"],
            state["request"]["area"],
            model=model,
        )
        state["design"] = str(path.relative_to(BASE_DIR))
        state["design_sha256"] = digest(path.read_bytes())
        protect(state, [path])
        state["stage"] = "review_design"
        save()
        return

    if stage == "review_design":
        if approve is None:
            return
        if approve != state["design_sha256"]:
            raise RuntimeError("표시한 설계 SHA-256과 다릅니다.")
        path = BASE_DIR / state["design"]
        approval = path.with_name("approval.json")
        if not approval.exists():
            design_plan.approve_design(path, approve)
        else:
            test_plan.read_approved_design(path)
        protect(state, [approval])
        state["stage"] = "generating_tests"
        save()
        candidate = generate_candidate(state, model)
        state["tests"] = str(candidate.relative_to(BASE_DIR))
        state["tests_sha256"] = digest(candidate.read_bytes())
        record = json.loads(candidate.read_text(encoding="utf-8"))
        protect(state, [
            candidate,
            *[
                candidate.parent / (item["filename"] + ".txt")
                for item in record["tests"]["files"]
            ],
        ])
        state["stage"] = "review_tests"
        save()
        return

    if stage == "review_tests":
        if feedback is not None:
            state["previous_tests"] = state["tests"]
            state["test_feedback"] = feedback
            state["stage"] = "generating_tests"
            save()
            candidate = generate_candidate(state, model)
            state["tests"] = str(candidate.relative_to(BASE_DIR))
            state["tests_sha256"] = digest(candidate.read_bytes())
            record = json.loads(candidate.read_text(encoding="utf-8"))
            protect(state, [
                candidate,
                *[
                    candidate.parent / (item["filename"] + ".txt")
                    for item in record["tests"]["files"]
                ],
            ])
            state["stage"] = "review_tests"
            save()
            return
        if confirm is None:
            return
        if confirm != state["tests_sha256"]:
            raise RuntimeError("표시한 테스트 SHA-256과 다릅니다.")
        path = BASE_DIR / state["tests"]
        confirmation = path.with_name("confirmation.json")
        if not confirmation.exists():
            test_plan.confirm_tests(path, confirm)
        else:
            implementation_link.read_confirmed(path, confirm)
        protect(state, [confirmation])
        state["stage"] = "installing"
        save()
        paths = implementation_link.install_tests(path, confirm)
        state["installed"] = {
            os.path.relpath(item, BASE_DIR): digest(item.read_bytes())
            for item in paths
        }
        state["stage"] = "waiting_git"
        save()
        return

    if stage == "waiting_git":
        if installed_tests(state):
            return
        path = implementation_link.create_plan(
            BASE_DIR / state["tests"], state["tests_sha256"]
        )
        state["plan"] = str(path.relative_to(BASE_DIR))
        state["plan_contract"] = plan_contract(path)
        state["stage"] = "execute"
        save()

    if state["stage"] == "execute":
        installed_tests_result = installed_tests(state)
        if installed_tests_result:
            raise RuntimeError("고정 테스트에 Git 변경이 있습니다.")
        path = BASE_DIR / state["plan"]
        status, details = plan_status(path)
        if status == "blocked":
            state["details"] = details
            save()
            return
        if status == "waiting_for_user" and answer_id is None:
            state["details"] = details
            save()
            return
        if status == "completed":
            if answer_id is not None:
                raise ValueError("완료된 계획에는 답변할 수 없습니다.")
            # 기존 실행기로 완료 산출물의 변경 여부도 확인한다.
            execute_plan.execute_plan(path, model=model)
        else:
            if answer_id is not None:
                if not any(item["id"] == answer_id for item in details):
                    raise ValueError("답변 대기 중인 작업 ID가 아닙니다.")
            execute_plan.execute_plan(
                path, model=model,
                answer_task_id=answer_id, answer=answer,
            )
        status, details = plan_status(path)
        state["details"] = details
        if status == "completed":
            state["stage"] = "completed"
        save()
        return

    if state["stage"] == "completed":
        if installed_tests(state):
            raise RuntimeError("완료 후 고정 테스트의 Git 상태가 변경됐습니다.")
        execute_plan.execute_plan(BASE_DIR / state["plan"], model=model)
        return

    if state["stage"] in ("generating_design", "generating_tests", "installing"):
        raise RuntimeError(
            "이전 단계가 중단됐습니다. 기록 확인이 필요하며 자동 반복하지 않습니다."
        )


def summarize(state, folder):
    result = {
        "stage": state["stage"],
        "record": str(folder),
    }
    if state["stage"] == "review_design":
        result.update({
            "review_file": str(BASE_DIR / state["design"]),
            "sha256": state["design_sha256"],
            "next": "--approve-design <위 SHA-256>",
        })
    elif state["stage"] == "review_tests":
        result.update({
            "review_file": str(BASE_DIR / state["tests"]),
            "sha256": state["tests_sha256"],
            "next": "--confirm-tests <위 SHA-256>",
        })
    elif state["stage"] == "waiting_git":
        pending = installed_tests(state)
        result["commit_required"] = pending
        result["next"] = (
            "표시한 테스트만 검토·커밋한 뒤 같은 명령 재실행"
            if pending else "같은 명령으로 구현 실행"
        )
    elif state["stage"] == "execute":
        status, details = plan_status(BASE_DIR / state["plan"])
        result["execution"] = status
        result["details"] = details
        if status == "waiting_for_user":
            result["next"] = "--answer <작업 ID> --answer-text <답변>"
    elif state["stage"] == "completed":
        result["next"] = "결과물을 확인하세요. 구현 코드는 자동 커밋하지 않습니다."
    return result


def workflow_folder(output, path, data, context):
    legacy = output / ("workflow_" + digest(str(path).encode("utf-8")))
    if legacy.is_symlink():
        raise ValueError("워크플로 기록에 심볼릭 링크를 사용할 수 없습니다.")
    legacy_state = legacy / "state.json"
    if legacy_state.is_file() and not legacy_state.is_symlink():
        state = json.loads(legacy_state.read_text(encoding="utf-8"))
        if (
            state.get("request_path") == str(path)
            and state.get("request_sha256") == digest(data)
            and state.get("context") == context
        ):
            return legacy

    identity = b"\0".join((
        str(path).encode("utf-8"),
        data,
        context.encode("utf-8"),
    ))
    return output / ("workflow_" + digest(identity))



def design_diagnostics(output: Path, started_at: set[Path]) -> list[DesignDiagnostic]:
    """Return only new, ordinary diagnostic records from this invocation."""
    records: list[DesignDiagnostic] = []
    for folder in output.glob("design_*"):
        if folder.is_symlink() or not folder.is_dir() or folder in started_at:
            continue
        attempts: list[DesignAttemptDiagnostic] = []
        for path in sorted(folder.glob("attempt_*.json")):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            if isinstance(record, dict):
                attempts.append({
                    "file": str(path),
                    "status": record.get("status"),
                    "error": record.get("error"),
                })
        if attempts:
            records.append({"folder": str(folder), "attempts": attempts})
    return sorted(records, key=lambda item: item["folder"])



def run_workflow(
    request_path, *, model=None, approve=None, confirm=None,
    answer_id=None, answer=None, retry=False, feedback=None, review_design=None,
):
    if feedback is not None and (
        not isinstance(feedback, str) or not feedback.strip()
        or len(feedback) > 4000
    ):
        raise ValueError("테스트 피드백은 1~4000자여야 합니다.")
    if sum(value is not None for value in (approve, confirm, answer_id, feedback, review_design)) > 1:
        raise ValueError("한 번에 승인·확정·답변 중 하나만 지정하세요.")
    if retry and any(
        value is not None for value in (approve, confirm, answer_id, answer, feedback, review_design)
    ):
        raise ValueError("--retry는 다른 승인·답변 옵션과 함께 사용할 수 없습니다.")
    path, data, request = load_request(request_path)
    context = edit_loop.read_context()
    output = BASE_DIR / "outputs"
    if BASE_DIR.is_symlink() or output.is_symlink():
        raise ValueError("도구·outputs 경로에 심볼릭 링크를 사용할 수 없습니다.")
    output.mkdir(exist_ok=True)

    lock = BASE_DIR / ".workflow.lock"
    try:
        with lock.open("x"):
            pass
    except FileExistsError:
        raise RuntimeError("워크플로 실행 중이거나 이전 실행이 강제 종료됐습니다.")

    try:
        # 같은 요청·문맥은 재개하고, 변경된 요청·문맥은 이전 기록을 보존한 새 실행으로 분리한다.
        folder = workflow_folder(output, path, data, context)
        if folder.is_symlink():
            raise ValueError("워크플로 기록에 심볼릭 링크를 사용할 수 없습니다.")
        folder.mkdir(exist_ok=True)
        state_path = folder / "state.json"
        if state_path.is_symlink():
            raise ValueError("상태 기록에 심볼릭 링크를 사용할 수 없습니다.")
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if (
                state["request_path"] != str(path)
                or state["request_sha256"] != digest(data)
                or state["context"] != context
                or state["request"] != request
            ):
                raise RuntimeError("요청 또는 작업 문맥이 변경됐습니다.")
        else:
            if any(folder.iterdir()):
                raise RuntimeError("상태 없는 기존 기록 폴더를 확인하세요.")
            state = {
                "request_path": str(path),
                "request_sha256": digest(data),
                "request": request,
                "context": context,
                "stage": "new",
                "protected": {},
            }
            write_state(state_path, state)

        check_protected(state)
        if retry:
            if state["stage"] not in ("generating_design", "generating_tests"):
                raise ValueError("설계·테스트 생성 중단만 명시적으로 재시도할 수 있습니다.")
            for name in (".edit_loop.lock", ".run_tasks.lock"):
                if (BASE_DIR / name).exists() or (BASE_DIR / name).is_symlink():
                    raise RuntimeError("다른 파일 작업 잠금이 있어 재시도하지 않습니다.")
            history = folder / ("retry_before_" + uuid.uuid4().hex + ".json")
            with history.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
            if state["stage"] == "generating_design":
                state["stage"] = "new"
            else:
                test_plan.read_approved_design(BASE_DIR / state["design"])
                state["stage"] = "review_design"
                approve = state["design_sha256"]
            write_state(state_path, state)
        # 출력 폴더 접근 실패는 기존 오류 처리 경로와 구분한다.
        existing_design_folders = set(output.glob("design_*"))
        log = folder / ("log_" + uuid.uuid4().hex + ".txt")

        def guard():
            if (
                path.is_symlink()
                or path.read_bytes() != data
                or edit_loop.read_context() != context
            ):
                raise RuntimeError("실행 중 요청 또는 문맥이 변경됐습니다.")
            check_protected(state)

        def guarded_model(prompt):
            guard()
            result = (edit_loop.ask_model if model is None else model)(prompt)
            guard()
            return result

        try:
            with log.open("x", encoding="utf-8") as stream:
                with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                    if review_design is not None:
                        connect_reviewed_design(state, state_path, review_design)
                    advance(
                        state, state_path, guarded_model,
                        approve, confirm, answer_id, answer, feedback,
                    )
            guard()
        except Exception as error:
            result = {
                "stage": state["stage"],
                "error": str(error),
                "record": str(folder),
                "log": str(log),
            }
            if state["stage"] == "generating_design":
                # 진단 기록 접근 실패가 원래 생성 오류를 가리지 않도록 한다.
                try:
                    diagnostics = design_diagnostics(output, existing_design_folders)
                except OSError:
                    diagnostics = []
                if diagnostics:
                    result["design_diagnostics"] = diagnostics
            with log.open("a", encoding="utf-8") as stream:
                stream.write("\n워크플로 오류: " + str(error) + "\n")
            return result
        result = summarize(state, folder)
        result["log"] = str(log)
        return result
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description="개인 게임 AI 단일 실행 흐름")
    parser.add_argument("--request", required=True, type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--approve-design")
    action.add_argument("--confirm-tests")
    action.add_argument("--answer", dest="answer_id")
    action.add_argument("--retry", action="store_true")
    action.add_argument("--test-feedback", type=Path)
    action.add_argument("--review-design", type=Path)
    parser.add_argument("--answer-text")
    args = parser.parse_args()
    if (args.answer_id is None) != (args.answer_text is None):
        parser.error("--answer와 --answer-text를 함께 지정하세요.")
    feedback = None
    if args.test_feedback:
        if args.test_feedback.is_symlink() or not args.test_feedback.is_file():
            parser.error("일반 피드백 파일이 필요합니다.")
        if args.test_feedback.stat().st_size > 16000:
            parser.error("피드백 파일이 너무 큽니다.")
        feedback = args.test_feedback.read_text(encoding="utf-8")
    result = run_workflow(
        args.request, approve=args.approve_design,
        confirm=args.confirm_tests,
        answer_id=args.answer_id, answer=args.answer_text,
        retry=args.retry, feedback=feedback, review_design=args.review_design,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if "error" in result:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
