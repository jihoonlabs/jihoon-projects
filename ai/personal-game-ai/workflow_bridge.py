"""Delegate one step to an explicitly selected generation checkout."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def run(request, tool_dir, *, approve=None, confirm=None, answer_id=None, answer=None, retry=False,
        feedback=None, review_design=None):
    if (answer_id is None) != (answer is None):
        raise ValueError("질문 ID와 답변을 함께 지정하세요.")
    if sum(value is not None for value in (approve, confirm, answer_id, feedback, review_design)) + bool(retry) > 1:
        raise ValueError("승인·확정·답변·재시도·검토 수정은 한 번에 하나만 지정하세요.")
    if answer is not None and (not isinstance(answer, str) or not answer.strip() or len(answer) > 4000):
        raise ValueError("답변은 1~4000자여야 합니다.")
    request = Path(request).absolute()
    tool_dir = Path(tool_dir).absolute()
    script = tool_dir / "workflow.py"
    if request.is_symlink() or not request.is_file():
        raise ValueError("일반 요청 파일이 필요합니다.")
    if tool_dir.is_symlink() or not tool_dir.is_dir() or script.is_symlink() or not script.is_file():
        raise ValueError("workflow.py가 있는 일반 도구 폴더를 지정하세요.")
    command = [sys.executable, str(script), "--request", str(request)]
    if approve is not None:
        command += ["--approve-design", approve]
    if confirm is not None:
        command += ["--confirm-tests", confirm]
    if answer_id is not None:
        command += ["--answer", answer_id, "--answer-text", answer]
    if retry:
        command += ["--retry"]
    for flag, value in (("--test-feedback", feedback), ("--review-design", review_design)):
        if value is None:
            continue
        # Resolve against the caller's cwd before switching to the engine cwd.
        path = Path(value).absolute()
        if path.is_symlink() or not path.is_file():
            raise ValueError("검토 자료는 일반 파일이어야 합니다.")
        if flag == "--test-feedback":
            if path.stat().st_size > 16000:
                raise ValueError("테스트 피드백 파일은 16000바이트 이내여야 합니다.")
            text = path.read_text(encoding="utf-8")
            if not text.strip() or len(text) > 4000:
                raise ValueError("테스트 피드백은 1~4000자여야 합니다.")
        command += [flag, str(path)]
    # The selected engine owns branch/context checks, locks and approval digests.
    # Do not import it here or replace its target.json with the intake config.
    completed = subprocess.run(command, cwd=tool_dir, capture_output=True,
                               text=True, encoding="utf-8", check=False)
    try:
        result = json.loads(completed.stdout)
    except (ValueError, TypeError):
        result = {"stage": "blocked", "error": completed.stderr[-2000:] or "workflow JSON 응답이 없습니다."}
    if not isinstance(result, dict) or not isinstance(result.get("stage"), str):
        result = {"stage": "blocked", "error": "workflow 응답 형식이 잘못됐습니다."}
    if completed.returncode and "error" not in result:
        result["error"] = "workflow가 실패 코드로 종료됐습니다."
    result["request_file"] = str(request)
    return result


def main():
    parser = argparse.ArgumentParser(description="준비된 요청으로 기존 workflow 시작·검토 재개")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--tool-dir", type=Path, required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--approve-design")
    action.add_argument("--confirm-tests")
    action.add_argument("--answer", dest="answer_id")
    action.add_argument("--retry", action="store_true")
    action.add_argument("--test-feedback", type=Path)
    action.add_argument("--review-design", type=Path)
    parser.add_argument("--answer-text")
    parser.add_argument("--interactive", action="store_true", help="모델 질문을 터미널에서 답하고 같은 요청으로 재개")
    args = parser.parse_args()
    try:
        result = run(args.request, args.tool_dir, approve=args.approve_design, confirm=args.confirm_tests,
                     answer_id=args.answer_id, answer=args.answer_text, retry=args.retry,
                     feedback=args.test_feedback, review_design=args.review_design)
        if args.interactive:
            result = continue_dialogue(args.request, args.tool_dir, result)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if "error" in result else 0


def continue_dialogue(request, tool_dir, result, *, ask=None, step=None, limit=20):
    """Answer execution questions only; never cross review/commit gates."""
    if ask is None:
        def ask(question):
            print(question + "\n답변 (/stop으로 중단):", file=sys.stderr, flush=True)
            line = sys.stdin.readline()
            return line.rstrip("\r\n") if line else None
    step = run if step is None else step
    count = 0
    while "error" not in result and result.get("stage") == "execute" and result.get("execution") == "waiting_for_user":
        if count >= limit:
            return {**result, "dialogue_paused": "question_limit"}
        details = result.get("details")
        if not isinstance(details, list) or not details or not all(
            isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip()
            and isinstance(item.get("question"), str) and item["question"].strip()
            for item in details
        ) or len({item["id"] for item in details}) != len(details):
            return {**result, "error": "workflow 질문 형식이 잘못됐습니다."}
        # Re-read the engine's latest question list after each answer.
        item = details[0]
        answer = ask("[" + item["id"] + "] " + item["question"])
        if answer is None or answer.strip() == "/stop":
            return {**result, "dialogue_paused": "user_stopped"}
        if not answer.strip() or len(answer) > 4000:
            return {**result, "dialogue_paused": "invalid_answer"}
        result = step(request, tool_dir, answer_id=item["id"], answer=answer)
        count += 1
    return result


if __name__ == "__main__":
    raise SystemExit(main())
