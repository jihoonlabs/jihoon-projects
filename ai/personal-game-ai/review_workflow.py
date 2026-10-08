"""Read-only diagnostics for an explicitly selected workflow record."""

import argparse
import json
import os
import subprocess
from pathlib import Path

import execute_plan
import workflow
from task_dependencies import order_tasks

STAGES = {
    "new", "generating_design", "review_design", "generating_tests",
    "review_tests", "installing", "waiting_git", "execute", "completed",
}
STATUSES = {"pending", "running", "failed", "waiting_for_user", "tests_passed"}


def record_state(record):
    base = workflow.BASE_DIR
    folder = Path(os.path.abspath(record))
    if folder.parent != base / "outputs" or not folder.name.startswith("workflow_"):
        raise ValueError("현재 도구의 outputs/workflow_* 기록 폴더를 지정하세요.")
    path = folder / "state.json"
    for item in (base, base / "outputs", folder, path):
        if item.is_symlink():
            raise ValueError("기록 경로에 심볼릭 링크를 사용할 수 없습니다.")
    if not path.is_file():
        raise ValueError("state.json이 없습니다. 실제 workflow 기록 폴더를 지정하세요.")
    if path.stat().st_size > 2_000_000:
        raise ValueError("2MB 이내의 일반 state.json이 필요합니다.")
    data = path.read_bytes()
    state = json.loads(data)
    if not isinstance(state, dict) or not {
        "request_path", "request_sha256", "request", "context", "stage", "protected"
    } <= state.keys():
        raise ValueError("워크플로 상태 필드가 잘못됐습니다.")
    if not isinstance(state["stage"], str) or state["stage"] not in STAGES:
        raise ValueError("알 수 없는 워크플로 단계입니다.")
    if not isinstance(state["protected"], dict):
        raise ValueError("보호 산출물 기록이 잘못됐습니다.")
    return path, data, state


def review(request_path, record):
    tasks = []
    report = {
        "read_only": True, "stage": None, "issues": [], "tasks": [],
        "next": "기록과 첫 오류를 확인하세요. 자동 재개하지 마세요.",
        "not_verified": ["이번 실행의 모델 생성", "Docker 테스트", "실제 Thumby 실행"],
    }
    try:
        state_path, original, state = record_state(record)
        report.update(stage=state["stage"], record=str(state_path.parent))
        locks = [
            name for name in (".workflow.lock", ".edit_loop.lock", ".run_tasks.lock")
            if (workflow.BASE_DIR / name).exists() or (workflow.BASE_DIR / name).is_symlink()
        ]
        if locks:
            raise RuntimeError("작업 잠금이 있습니다. 삭제하지 말고 실행 여부를 확인하세요: " + ", ".join(locks))
        request, data, payload = workflow.load_request(request_path)
        context = workflow.edit_loop.read_context()
        matches = {
            "request_path": state["request_path"] == str(request),
            "request_sha256": state["request_sha256"] == workflow.digest(data),
            "request": state["request"] == payload,
            "context": state["context"] == context,
        }
        report["matches"] = matches
        if not all(matches.values()):
            report["issues"].append("요청/문맥 불일치: " + ", ".join(key for key, ok in matches.items() if not ok))
        workflow.check_protected(state)
        report["protected_artifacts"] = "unchanged"
        if state["stage"] in {"review_design", "review_tests"}:
            kind = "design" if state["stage"] == "review_design" else "tests"
            relative = state.get(kind)
            expected = state.get(kind + "_sha256")
            if (
                not isinstance(relative, str) or not relative
                or Path(relative).is_absolute() or ".." in Path(relative).parts
                or not isinstance(expected, str) or len(expected) != 64
                or state["protected"].get(relative) != expected
            ):
                raise ValueError("검토 후보 경로·SHA·보호 기록이 없거나 일치하지 않습니다.")
            report["review_file"] = str(workflow.BASE_DIR / relative)
            report["review_sha256"] = expected
        if state["stage"] in {"waiting_git", "execute", "completed"} and "installed" not in state:
            raise ValueError("설치한 고정 테스트 기록이 없습니다.")
        if "installed" in state:
            if not isinstance(state["installed"], dict) or not state["installed"]:
                raise ValueError("설치한 고정 테스트 기록이 비어 있거나 잘못됐습니다.")
            report["commit_required"] = workflow.installed_tests(state)
            if report["commit_required"] and state["stage"] in {"execute", "completed"}:
                report["issues"].append("실행/완료 기록의 고정 테스트 Git 보호가 일치하지 않습니다.")
        if "plan" in state:
            path = execute_plan.resolve_plan(workflow.BASE_DIR / state["plan"])
            plan_data = path.read_bytes()
            tasks = order_tasks(json.loads(plan_data))
            by_id = {task["id"]: task for task in tasks}
            for task in tasks:
                if task.get("status") not in STATUSES:
                    raise ValueError("알 수 없는 작업 상태입니다: " + task["id"])
                item = {key: task.get(key) for key in ("id", "target", "status")}
                report["tasks"].append(item)
                if task["status"] == "tests_passed":
                    execute_plan.check_artifact(task)
                    item["artifact"] = "unchanged"
                elif task["status"] in {"running", "failed"}:
                    item["error"] = task.get("error", "이전 실행 중단 상태 확인 필요")
                    report["issues"].append("중단/실패 작업: " + task["id"])
                elif task["status"] == "waiting_for_user":
                    item["question"] = task.get("question")
                if task["status"] == "pending" and all(
                    by_id[name]["status"] == "tests_passed"
                    for name in task.get("depends_on", [])
                ):
                    item["request_chars"] = len(execute_plan.dependency_request(task, by_id))
            if state["stage"] == "completed" and any(task["status"] != "tests_passed" for task in tasks):
                report["issues"].append("completed 기록과 작업 상태가 일치하지 않습니다.")
            if path.read_bytes() != plan_data:
                raise RuntimeError("검토 중 계획 기록이 변경됐습니다.")
        elif state["stage"] in {"execute", "completed"}:
            raise ValueError("실행 단계에 계획 기록이 없습니다.")

        # 진단 도중 변경된 기록을 일관된 결과로 보고하지 않는다.
        workflow.check_protected(state)
        for task in tasks:
            if task["status"] == "tests_passed":
                execute_plan.check_artifact(task)
        if state_path.read_bytes() != original or request.read_bytes() != data or workflow.edit_loop.read_context() != context:
            raise RuntimeError("검토 중 상태·요청·문맥이 변경됐습니다.")
        if tasks and path.read_bytes() != plan_data:
            raise RuntimeError("검토 종료 시 계획 상태가 변경됐습니다.")
        if any((workflow.BASE_DIR / name).exists() or (workflow.BASE_DIR / name).is_symlink() for name in (
            ".workflow.lock", ".edit_loop.lock", ".run_tasks.lock"
        )):
            raise RuntimeError("검토 중 작업 잠금이 생겼습니다. 실행 종료 후 다시 검사하세요.")
        if state["stage"] in {"generating_design", "generating_tests", "installing"}:
            report["issues"].append("중단 가능성이 있는 단계입니다. 기록과 로그를 먼저 확인하세요.")
        if not report["issues"]:
            if report.get("commit_required"):
                report["next"] = "표시한 고정 테스트를 검토하고 Git 준비를 완료하세요."
            elif state["stage"] == "completed":
                report["next"] = "현재 코드와 저장된 검증 artifact는 일치합니다. 모델을 재호출하기 전에 게임 테스트·Docker·실기 결과를 확인하세요."
            elif state["stage"] in {"review_design", "review_tests"}:
                report["next"] = "현재 설계/테스트 후보 내용을 검토한 뒤 해당 SHA로 승인/확정하세요."
            elif any(item["status"] == "waiting_for_user" for item in report["tasks"]):
                report["next"] = "표시한 질문에 답변한 뒤 기존 workflow를 재개하세요."
            else:
                report["next"] = "읽기 검사에서 차단 사유가 없습니다. 모델·Docker 준비를 확인한 뒤 기존 workflow를 재개하세요."
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.SubprocessError) as error:
        report["issues"].append(str(error))
    report["result"] = "blocked" if report["issues"] else "reviewed"
    return report


def main():
    parser = argparse.ArgumentParser(description="워크플로 결과 읽기 전용 검사; 모델·Docker·상태 변경 없음")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--record", required=True, type=Path)
    args = parser.parse_args()
    report = review(args.request, args.record)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
