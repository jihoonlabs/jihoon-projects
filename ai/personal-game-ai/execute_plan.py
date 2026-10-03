import argparse
import json
from pathlib import Path

import run_tasks

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


def execute_plan(path, model=None, answer_task_id=None, answer=None):
    path = resolve_plan(path)
    tasks = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 8:
        raise ValueError("계획 작업은 1~8개여야 합니다.")

    targets = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("작업은 JSON 객체여야 합니다.")
        if task.get("kind") not in ("edit", "create"):
            raise ValueError("계획은 edit/create 작업만 실행합니다.")
        run_tasks.validate_request(task)
        target = task["target"]
        if target in targets:
            raise ValueError("같은 대상의 작업을 중복 실행할 수 없습니다.")
        targets.add(target)
        if task.get("status") == "failed":
            raise RuntimeError("실패한 작업이 있습니다. 원인 확인 후 중단합니다.")

    # 전용 CLI 프로세스에서 목록만 바꾸고 기존 잠금·재개를 재사용한다.
    original = run_tasks.TASKS_PATH
    try:
        run_tasks.TASKS_PATH = path
        return run_tasks.run_tasks(
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