import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from ask_ai import ask_model
from read_context import read_context

BASE_DIR = Path(__file__).resolve().parent
SANDBOX = BASE_DIR / "sandbox"
TARGET = SANDBOX / "clamp.py"
TEST = SANDBOX / "test_clamp.py"
MAX_ATTEMPTS = 3


def run_test(log_path):
    name = "game-ai-test-" + uuid.uuid4().hex
    command = [
        "docker", "run", "--rm",
        "--name", name,
        "--network", "none",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--memory", "256m",
        "--cpus", "1",
        "--pids-limit", "64",
        "--user", "65534:65534",
        "--mount",
        f"type=bind,source={SANDBOX},target=/work,readonly",
        "--workdir", "/work",
        "python:3.11-slim",
        "python", "-B", "-m", "unittest", "-v", "test_clamp",
    ]

    # 出力はファイルへ保存し、モデルには末尾だけを渡す。
    try:
        with log_path.open("w", encoding="utf-8") as log:
            result = subprocess.run(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
        feedback = log_path.read_text(encoding="utf-8")[-6000:]
        return result.returncode == 0, feedback
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["docker", "rm", "-f", name],
            capture_output=True,
            timeout=10,
        )
        raise RuntimeError("테스트가 30초를 초과해 중단됐습니다.")


def main():
    context = read_context()
    if TARGET.is_symlink() or TEST.is_symlink():
        raise RuntimeError("시험 파일에 심볼릭 링크를 사용할 수 없습니다.")

    original = TARGET.read_text(encoding="utf-8")
    fixed_test = TEST.read_bytes()

    # 同時実行による上書きを防ぐ。
    lock = BASE_DIR / ".edit_loop.lock"
    try:
        lock.open("x").close()
    except FileExistsError:
        raise RuntimeError(
            "실행 중이거나 이전 실행이 중단됐습니다. "
            ".edit_loop.lock을 확인하세요."
        )

    try:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output = BASE_DIR / "outputs" / f"edit_{stamp}"
        output.mkdir(parents=True)
        (output / "original.py").write_text(original, encoding="utf-8")
        current = original
        feedback = "아직 검사하지 않았습니다."

        for attempt in range(1, MAX_ATTEMPTS + 1):
            # 実行中に人が編集した場合も上書きしない。
            if TARGET.read_text(encoding="utf-8") != current:
                raise RuntimeError("수정 대상이 외부에서 변경됐습니다.")
            if TEST.read_bytes() != fixed_test:
                raise RuntimeError("고정 테스트가 변경됐습니다.")
            if read_context() != context:
                raise RuntimeError("브랜치 또는 작업 문맥이 변경됐습니다.")

            prompt = (
                context
                + "\n\n다음 시험용 함수 하나를 구현하세요.\n"
                "clamp(value, minimum, maximum): 범위 밖이면 가까운 "
                "경곗값, 범위 안이면 원래 값을 반환합니다. "
                "minimum <= maximum을 가정합니다.\n"
                "파일·네트워크·프로세스 접근은 필요하지 않습니다.\n"
                "실제로 수정하거나 테스트했다고 주장하지 마세요.\n"
                "응답은 Markdown 없이 JSON 객체 하나만 출력하세요.\n"
                '구현할 수 있으면 {"action":"edit","code":"전체 Python 코드"}\n'
                '사용자 결정이 필요하면 {"action":"question",'
                '"question":"한국어 질문"}\n'
                "\n현재 코드:\n" + current
                + "\n이전 검사 결과:\n" + feedback
            )

            print(f"AI 수정 시도 {attempt}/{MAX_ATTEMPTS}", flush=True)
            answer = ask_model(prompt)
            (output / f"answer_{attempt}.txt").write_text(
                answer, encoding="utf-8"
            )

            try:
                proposal = json.loads(answer)
                if not isinstance(proposal, dict):
                    raise ValueError("JSON 객체가 필요합니다.")

                if proposal.get("action") == "question":
                    question = proposal.get("question")
                    if not isinstance(question, str) or not question.strip():
                        raise ValueError("질문이 비어 있습니다.")
                    print("확인 필요:", question)
                    print("기록 위치:", output)
                    return

                if proposal.get("action") != "edit":
                    raise ValueError("action은 edit 또는 question이어야 합니다.")
                code = proposal.get("code")
                if not isinstance(code, str) or not code.strip():
                    raise ValueError("코드가 비어 있습니다.")
                compile(code, str(TARGET), "exec")
            except (ValueError, SyntaxError) as error:
                feedback = f"응답 형식 또는 문법 오류: {error}"
                print(feedback)
                continue

            # モデル待機中の変更も確認してから書き込む。
            if TARGET.read_text(encoding="utf-8") != current:
                raise RuntimeError("수정 대상이 외부에서 변경됐습니다.")
            if TEST.read_bytes() != fixed_test or read_context() != context:
                raise RuntimeError("테스트 또는 작업 문맥이 변경됐습니다.")

            current = code.rstrip() + "\n"
            (output / f"candidate_{attempt}.py").write_text(
                current, encoding="utf-8"
            )
            TARGET.write_text(current, encoding="utf-8")

            passed, feedback = run_test(output / f"test_{attempt}.txt")
            print(feedback)
            if passed:
                print("지정 테스트 통과. 수정 반복 종료.")
                print("기록 위치:", output)
                return

        print("3회 시도 종료. 사용자 확인이 필요합니다.")
        print("원본·시도·검사 기록:", output)
    finally:
        lock.unlink()


if __name__ == "__main__":
    main()