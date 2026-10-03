import argparse
import hashlib
import json
from pathlib import Path

import edit_loop
import run_tasks
from task_dependencies import order_tasks

BASE_DIR = Path(__file__).resolve().parent


def resolve_plan(path):
    path = Path(path).absolute()
    output = BASE_DIR / "outputs"
    if (
        path.name != "tasks.json"
        or path.parent.parent != output
        or not path.parent.name.startswith("plan_")
    ):
        raise ValueError("outputs/plan_*/tasks.json만 실행할 수 있습니다.")
    for candidate in (BASE_DIR, output, path.parent, path):
        if candidate.is_symlink():
            raise ValueError("계획 경로에 심볼릭 링크를 사용할 수 없습니다.")
    if not path.is_file():
        raise ValueError("계획 파일이 없습니다.")
    return path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def capture_artifact(task):
    target, test = edit_loop.resolve_files(
        task["target"], task["test_module"]
    )
    edit_loop.check_git_files(test, test)
    data = target.read_bytes()
    code = data.decode("utf-8")
    return {
        "code": code,
        "sha256": digest(data),
        "test_sha256": digest(test.read_bytes()),
    }


def check_artifact(task):
    artifact = task.get("artifact")
    if not isinstance(artifact, dict) or set(artifact) != {
        "code", "sha256", "test_sha256"
    }:
        raise RuntimeError("선행 작업의 검증 코드 기록이 없습니다.")
    if not isinstance(artifact["code"], str):
        raise RuntimeError("선행 코드 기록이 잘못됐습니다.")
    current = capture_artifact(task)
    if current != artifact:
        raise RuntimeError(
            f"검증 후 선행 파일 또는 테스트가 변경됐습니다: {task['id']}"
        )
    return artifact["code"]


def dependency_request(task, by_id):
    request = run_tasks.task_request(task)
    for dependency_id in task.get("depends_on", []):
        dependency = by_id[dependency_id]
        if dependency["status"] != "tests_passed":
            raise RuntimeError("선행 작업이 통과하지 않았습니다.")
        code = check_artifact(dependency)
        request += (
            "\n\n# 검증된 선행 코드: "
            + dependency["target"] + "\n" + code
        )
    if len(request) > 4000:
        raise ValueError("선행 코드와 답변을 포함한 요청이 4000자를 넘습니다.")
    return request


def run_dependent_plan(model=None, answer_task_id=None, answer=None):
    model = edit_loop.ask_model if model is None else model
    lock = run_tasks.BASE_DIR / ".run_tasks.lock"
    try:
        lock.open("x").close()
    except FileExistsError:
        raise RuntimeError("작업 목록이 실행 중이거나 중단 상태입니다.")

    try:
        context = run_tasks.read_context()
        tasks = order_tasks(run_tasks.load_tasks())
        by_id = {task["id"]: task for task in tasks}

        def check_context():
            if run_tasks.read_context() != context:
                raise RuntimeError("브랜치 또는 작업 문맥이 변경됐습니다.")

        for task in tasks:
            if task["status"] == "running":
                print(f"확인 필요 [{task['id']}]: 이전 실행이 중단됐습니다.")
                return
            if task["status"] == "failed":
                raise RuntimeError("실패한 작업이 있어 실행을 중단합니다.")
            if task["status"] == "tests_passed":
                check_artifact(task)

        # 실행 전에 모든 미완료 대상의 기존 보호 검사를 수행한다.
        for task in tasks:
            if task["status"] in ("pending", "waiting_for_user"):
                run_tasks.prepare_file_task(task)

        if answer_task_id is not None:
            task = by_id.get(answer_task_id)
            if task is None or task["status"] != "waiting_for_user":
                raise ValueError("답변 대기 중인 작업 ID가 필요합니다.")
            if answer is None:
                print(f"확인 필요 [{task['id']}]: {task['question']}")
                answer = input("답변: ")
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("답변은 비어 있지 않은 문자열이어야 합니다.")
            updated = {
                **task,
                "answers": [
                    *task.get("answers", []),
                    {"question": task["question"], "answer": answer.strip()},
                ],
                "status": "pending",
            }
            request = dependency_request(updated, by_id)
            probe = {**updated, "prompt": request, "answers": []}
            run_tasks.prepare_file_task(probe)
            check_context()
            task.update(updated)
            run_tasks.save_tasks(tasks)
        elif answer is not None:
            raise ValueError("답변할 작업 ID가 필요합니다.")

        for task in tasks:
            if task["status"] == "waiting_for_user":
                print(f"확인 필요 [{task['id']}]: {task['question']}")
                return

        run_tasks.OUTPUT_DIR.mkdir(exist_ok=True)
        for task in tasks:
            if task["status"] != "pending":
                continue
            check_context()
            request = dependency_request(task, by_id)
            working = {
                **task,
                "prompt": request,
                "answers": [],
            }
            run_tasks.prepare_file_task(working)
            task["status"] = "running"
            for key in (
                "error", "cleanup_error", "question",
                "output", "attempts", "artifact",
            ):
                task.pop(key, None)
                working.pop(key, None)
            run_tasks.save_tasks(tasks)

            def check_dependencies():
                check_context()
                for dependency_id in task.get("depends_on", []):
                    check_artifact(by_id[dependency_id])

            def guarded_model(prompt):
                check_dependencies()
                response = model(prompt)
                check_dependencies()
                return response

            print(f"작업 {task['id']} 처리 중...", flush=True)
            try:
                check_dependencies()
                run_tasks.handle_edit(working, guarded_model)
                check_dependencies()
                for key in (
                    "status", "output", "question", "error",
                    "cleanup_error", "attempts",
                ):
                    if key in working:
                        task[key] = working[key]
                if task["status"] == "tests_passed":
                    task["artifact"] = capture_artifact(task)
            except Exception as error:
                task["status"] = "failed"
                task["error"] = str(error)
                run_tasks.save_tasks(tasks)
                raise

            run_tasks.save_tasks(tasks)
            print(f"작업 {task['id']}: {task['status']}")
            if task.get("question"):
                print("확인 필요:", task["question"])
            if task["status"] != "tests_passed":
                return
        print("의존성 작업 목록 처리 종료")
    finally:
        lock.unlink()


def execute_plan(path, model=None, answer_task_id=None, answer=None):
    path = resolve_plan(path)
    tasks = json.loads(path.read_text(encoding="utf-8"))
    tasks = order_tasks(tasks)

    targets = set()
    for task in tasks:
        if task.get("kind") not in ("edit", "create"):
            raise ValueError("계획은 edit/create 작업만 실행합니다.")
        run_tasks.validate_request(task)
        target = task["target"]
        if target in targets:
            raise ValueError("같은 대상의 작업을 중복 실행할 수 없습니다.")
        targets.add(target)
        if task.get("status") == "failed":
            raise RuntimeError("실패한 작업이 있습니다. 원인 확인 후 중단합니다.")

    original = run_tasks.TASKS_PATH
    try:
        run_tasks.TASKS_PATH = path
        runner = (
            run_dependent_plan
            if any(task.get("depends_on") for task in tasks)
            else run_tasks.run_tasks
        )
        return runner(
            model=model,
            answer_task_id=answer_task_id,
            answer=answer,
        )
    finally:
        run_tasks.TASKS_PATH = original


def main():
    parser = argparse.ArgumentParser(description="생성된 작업 계획 실행")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--answer", dest="answer_task_id")
    args = parser.parse_args()
    execute_plan(args.plan, answer_task_id=args.answer_task_id)


if __name__ == "__main__":
    main()