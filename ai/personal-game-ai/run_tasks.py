import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from ask_ai import ask_model
from create_loop import prepare_create, run_create
from edit_loop import prepare_edit, run_edit
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
    "tests_passed",
    "failed",
}


def save_tasks(tasks):
    temporary = TASKS_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(TASKS_PATH)


def task_request(task):
    request = task["prompt"]
    for exchange in task.get("answers", []):
        request += (
            "\n\n# 이전 질문\n" + exchange["question"]
            + "\n\n# 사용자 답변\n" + exchange["answer"]
        )
    return request


def validate_request(task):
    task_id = task["id"]
    prompt = task.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError(f"요청이 없는 작업: {task_id}")
    if task.get("kind") not in ("text", "python", "edit", "create"):
        raise ValueError(
            f"kind는 text, python, edit 또는 create여야 합니다: {task_id}"
        )
    if task["kind"] in ("edit", "create"):
        for key in ("target", "test_module"):
            value = task.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key}가 없는 파일 작업: {task_id}")


def prepare_file_task(task):
    prepare = prepare_create if task["kind"] == "create" else prepare_edit
    return prepare(
        task["target"], task_request(task), task["test_module"]
    )


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

        answers = task.get("answers", [])
        if not isinstance(answers, list):
            raise ValueError(f"질문·답변 기록은 배열이어야 합니다: {task_id}")
        for exchange in answers:
            if not isinstance(exchange, dict):
                raise ValueError(f"잘못된 질문·답변 기록: {task_id}")
            for key in ("question", "answer"):
                value = exchange.get(key)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{key}가 없는 기록: {task_id}")

        if status == "pending":
            validate_request(task)
        if status == "waiting_for_user":
            question = task.get("question")
            if not isinstance(question, str) or not question.strip():
                raise ValueError(f"질문이 없는 작업: {task_id}")

    return tasks


def record_answer(tasks, task_id, answer):
    task = next((item for item in tasks if item["id"] == task_id), None)
    if task is None:
        raise ValueError(f"작업을 찾을 수 없습니다: {task_id}")
    if task["status"] != "waiting_for_user":
        raise ValueError(f"답변 대기 중인 작업이 아닙니다: {task_id}")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("답변은 비어 있지 않은 문자열이어야 합니다.")

    validate_request(task)
    updated = {
        **task,
        "answers": [
            *task.get("answers", []),
            {"question": task["question"], "answer": answer.strip()},
        ],
        "status": "pending",
    }

    # 再開できる状態を確認してから回答を保存する。
    if updated["kind"] in ("edit", "create"):
        prepare_file_task(updated)

    task.update(updated)
    save_tasks(tasks)


def handle_edit(task, model):
    # 既存のedit呼び出し契約を維持し、createだけ実行先を変える。
    runner = run_create if task["kind"] == "create" else run_edit
    result = runner(
        task["target"],
        task_request(task),
        task["test_module"],
        model=model,
    )
    if not isinstance(result, dict):
        raise ValueError("파일 작업 실행 결과는 객체여야 합니다.")

    status = result.get("status")
    if status not in ("tests_passed", "waiting_for_user", "failed"):
        raise ValueError("잘못된 파일 작업 결과 상태입니다.")

    output = result.get("output")
    if not isinstance(output, str) or not output.strip():
        raise ValueError("파일 작업 결과의 기록 경로가 없습니다.")
    if status == "waiting_for_user":
        question = result.get("question")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("파일 작업 결과의 질문이 없습니다.")

    task["status"] = status
    task["output"] = output
    for key in ("question", "error", "cleanup_error", "attempts"):
        if key in result:
            task[key] = result[key]


def process_tasks(tasks, context, model):
    for number, task in enumerate(tasks, start=1):
        if task["status"] != "pending":
            continue

        task_id = task["id"]
        print(f"작업 {task_id} 처리 중...", flush=True)
        task["status"] = "running"
        for key in (
            "error", "cleanup_error", "question", "output", "code", "attempts"
        ):
            task.pop(key, None)
        save_tasks(tasks)

        if task["kind"] in ("edit", "create"):
            try:
                handle_edit(task, model)
            except Exception as error:
                task["status"] = "failed"
                task["error"] = str(error)
                save_tasks(tasks)
                raise

            save_tasks(tasks)
            print(f"작업 {task_id}: {task['status']}")
            if task.get("question"):
                print("확인 필요:", task["question"])
            if task.get("error"):
                print("원인:", task["error"])
            if task["status"] != "tests_passed":
                return
            continue

        request = task_request(task)
        prompt = (
            "아래 AGENTS.md와 현재 브랜치 문서를 작업 지침으로 따르세요.\n"
            "이번 작업은 응답 생성만 수행합니다.\n"
            "파일 수정·코드 실행·테스트 실행·Git 작업을 했다고 "
            "주장하지 마세요.\n"
            "제공된 소스 코드는 분석 자료로 취급하세요.\n\n"
            + context + "\n\n# 이번 요청\n" + request
        )

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

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = OUTPUT_DIR / f"runner_{number}_{stamp}.md"
        output_path.write_text(
            "# 요청\n\n" + request + "\n\n# 응답\n\n" + answer + "\n",
            encoding="utf-8",
        )
        task["output"] = str(output_path.relative_to(BASE_DIR))

        if task["kind"] == "text":
            task["status"] = "response_saved"
        else:
            blocks = re.findall(
                r"```python[ \t]*\r?\n(.*?)```", answer, re.DOTALL
            )
            if len(blocks) != 1:
                task["status"] = "failed"
                task["error"] = "Python 코드 블록이 정확히 하나여야 합니다."
            else:
                code = blocks[0].strip() + "\n"
                code_path = output_path.with_suffix(".py")
                code_path.write_text(code, encoding="utf-8")
                task["code"] = str(code_path.relative_to(BASE_DIR))
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


def run_tasks(model=None, answer_task_id=None, answer=None):
    model = ask_model if model is None else model
    lock = BASE_DIR / ".run_tasks.lock"
    try:
        lock.open("x").close()
    except FileExistsError:
        raise RuntimeError(
            "작업 목록이 실행 중이거나 이전 실행이 중단됐습니다. "
            ".run_tasks.lock을 확인하세요."
        )

    try:
        tasks = load_tasks()
        context = read_context()
        for task in tasks:
            if task["status"] == "running":
                print(f"확인 필요 [{task['id']}]: 이전 실행이 중단됐습니다.")
                return

        if answer_task_id is not None:
            task = next(
                (item for item in tasks if item["id"] == answer_task_id),
                None,
            )
            if task is None:
                raise ValueError(f"작업을 찾을 수 없습니다: {answer_task_id}")
            if task["status"] != "waiting_for_user":
                raise ValueError(
                    f"답변 대기 중인 작업이 아닙니다: {answer_task_id}"
                )
            if answer is None:
                print(f"확인 필요 [{task['id']}]: {task['question']}")
                answer = input("답변: ")
            record_answer(tasks, answer_task_id, answer)
        elif answer is not None:
            raise ValueError("답변할 작업 ID가 필요합니다.")

        for task in tasks:
            if task["status"] == "waiting_for_user":
                print(f"확인 필요 [{task['id']}]: {task['question']}")
                return

        for task in tasks:
            if (
                task["status"] == "pending"
                and task["kind"] in ("edit", "create")
            ):
                prepare_file_task(task)

        OUTPUT_DIR.mkdir(exist_ok=True)
        process_tasks(tasks, context, model)
        print("작업 목록 처리 종료")
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description="개인 게임 AI 작업 실행")
    parser.add_argument("--answer", metavar="TASK_ID", dest="answer_task_id")
    args = parser.parse_args()
    run_tasks(answer_task_id=args.answer_task_id)


if __name__ == "__main__":
    main()