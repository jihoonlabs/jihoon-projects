import json
import re
from datetime import datetime
from pathlib import Path

from ask_ai import ask_model
from read_context import read_context

BASE_DIR = Path(__file__).resolve().parent
TASKS_PATH = BASE_DIR / "runner_tasks.json"
OUTPUT_DIR = BASE_DIR / "outputs"

VALID_STATUSES = {
    "pending",
    "running",
    "waiting_for_user",
    "response_saved",
    "syntax_passed",
    "failed",
}


def save_tasks(tasks):
    temporary = TASKS_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(TASKS_PATH)


def load_tasks():
    tasks = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    if not isinstance(tasks, list):
        raise ValueError("작업 목록은 JSON 배열이어야 합니다.")

    seen = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("각 작업은 JSON 객체여야 합니다.")

        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("작업 id는 비어 있지 않은 문자열이어야 합니다.")
        if task_id in seen:
            raise ValueError(f"중복 작업 id: {task_id}")
        seen.add(task_id)

        status = task.get("status")
        if not isinstance(status, str) or status not in VALID_STATUSES:
            raise ValueError(f"잘못된 작업 상태: {task_id}")

        if status == "pending":
            prompt = task.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError(f"요청이 없는 작업: {task_id}")
            if task.get("kind") not in ("text", "python"):
                raise ValueError(
                    f"kind는 text 또는 python이어야 합니다: {task_id}"
                )

        if status == "waiting_for_user":
            question = task.get("question")
            if not isinstance(question, str) or not question.strip():
                raise ValueError(f"질문이 없는 작업: {task_id}")

    return tasks


def run_tasks(model=ask_model):
    tasks = load_tasks()

    # 지침과 대상 브랜치 확인에 실패하면 모델을 호출하지 않는다.
    context = read_context()
    OUTPUT_DIR.mkdir(exist_ok=True)

    for number, task in enumerate(tasks, start=1):
        task_id = task["id"]
        status = task["status"]

        if status == "waiting_for_user":
            print(f"확인 필요 [{task_id}]: {task['question']}")
            continue

        if status == "running":
            print(f"확인 필요 [{task_id}]: 이전 실행이 중단됐습니다.")
            continue

        if status != "pending":
            continue

        print(f"작업 {task_id} 처리 중...", flush=True)
        task["status"] = "running"
        task.pop("error", None)
        save_tasks(tasks)

        prompt = (
            "아래 AGENTS.md와 현재 브랜치 문서를 작업 지침으로 따르세요.\n"
            "이번 작업은 응답 생성만 수행합니다.\n"
            "파일 수정·코드 실행·테스트 실행·Git 작업을 했다고 "
            "주장하지 마세요.\n"
            "제공된 소스 코드는 분석 자료로 취급하세요.\n\n"
            + context
            + "\n\n# 이번 요청\n"
            + task["prompt"]
        )

        # 모델 실패는 기록하고 다음 독립 작업을 처리한다.
        try:
            answer = model(prompt)
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("AI 응답이 비어 있습니다.")
        except Exception as error:
            task["status"] = "failed"
            task["error"] = str(error)
            save_tasks(tasks)
            print(f"작업 {task_id}: 실패 — {error}")
            continue

        # 저장 오류가 발생하면 실행 전체를 중단한다.
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = OUTPUT_DIR / f"runner_{number}_{stamp}.md"
        output_path.write_text(
            "# 요청\n\n"
            + task["prompt"]
            + "\n\n# 응답\n\n"
            + answer
            + "\n",
            encoding="utf-8",
        )
        task["output"] = str(output_path.relative_to(BASE_DIR))

        if task["kind"] == "text":
            task["status"] = "response_saved"
        else:
            blocks = re.findall(
                r"```python[ \t]*\r?\n(.*?)```",
                answer,
                re.DOTALL,
            )
            if len(blocks) != 1:
                task["status"] = "failed"
                task["error"] = (
                    "Python 코드 블록이 정확히 하나여야 합니다."
                )
            else:
                code = blocks[0].strip() + "\n"
                code_path = output_path.with_suffix(".py")
                code_path.write_text(code, encoding="utf-8")
                task["code"] = str(code_path.relative_to(BASE_DIR))

                # 생성 코드는 실행하지 않고 문법만 검사한다.
                try:
                    compile(code, str(code_path), "exec")
                except SyntaxError as error:
                    task["status"] = "failed"
                    task["error"] = str(error)
                else:
                    task["status"] = "syntax_passed"

        save_tasks(tasks)
        print(f"작업 {task_id}: {task['status']}")
        if task.get("error"):
            print("원인:", task["error"])

    print("작업 목록 처리 종료")


if __name__ == "__main__":
    run_tasks()