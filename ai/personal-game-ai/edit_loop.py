import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from ask_ai import ask_model
from read_context import CONFIG_PATH, git_output, read_context

BASE_DIR = Path(__file__).resolve().parent
SANDBOX = BASE_DIR / "sandbox"

# テストでは一時ディレクトリへ差し替える。本番は設定から取得する。
GAME_DIR = None
MAX_ATTEMPTS = 3

DEFAULT_REQUEST = (
    "clamp(value, minimum, maximum) 함수를 구현하세요. "
    "범위 밖이면 가까운 경곗값, 범위 안이면 원래 값을 반환합니다. "
    "minimum <= maximum을 가정합니다."
)


def game_location():
    if GAME_DIR is not None:
        return Path(GAME_DIR), BASE_DIR.parent.parent

    config_path = Path(CONFIG_PATH).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("설정은 JSON 객체여야 합니다.")

    root_value = config.get("repository_root")
    if not isinstance(root_value, str) or not root_value.strip():
        raise ValueError("repository_root 설정이 필요합니다.")
    root = (config_path.parent / root_value).resolve()
    actual_root = Path(
        git_output(root, "rev-parse", "--show-toplevel")
    ).resolve()
    if root != actual_root:
        raise ValueError("repository_root는 저장소 최상단이어야 합니다.")

    value = config.get("edit_directory")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "게임 수정은 edit_directory를 명시한 설정에서만 허용합니다."
        )
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("edit_directory는 저장소 내부 상대 경로여야 합니다.")

    directory = root / relative
    if directory.resolve() == root:
        raise ValueError("저장소 최상단을 수정 폴더로 지정할 수 없습니다.")
    if root not in directory.resolve().parents:
        raise ValueError("게임 수정 폴더가 저장소 밖에 있습니다.")

    return directory, root


def check_directory(directory):
    directory = Path(directory)
    if directory == SANDBOX:
        anchor = BASE_DIR
    else:
        allowed, anchor = game_location()
        if directory != allowed:
            raise ValueError("허용되지 않은 검사 폴더입니다.")

    # OS側のリンクは対象外とし、プロジェクト内の経路だけを検査する。
    relative = directory.relative_to(anchor)
    current = anchor
    if current.is_symlink():
        raise ValueError("프로젝트 경로에 심볼릭 링크를 사용할 수 없습니다.")
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("대상 폴더에 심볼릭 링크를 사용할 수 없습니다.")
    if not directory.is_dir():
        raise ValueError("검사 폴더가 없습니다.")


def resolve_files(target_file, test_module):
    if not isinstance(target_file, str) or not target_file.strip():
        raise ValueError("수정 대상 경로가 필요합니다.")
    if not isinstance(test_module, str) or not test_module.isidentifier():
        raise ValueError("테스트 모듈은 Python 식별자여야 합니다.")
    if not test_module.startswith("test_"):
        raise ValueError("테스트 모듈 이름은 test_로 시작해야 합니다.")

    relative = Path(target_file)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or len(relative.parts) != 2
        or relative.parts[0] not in ("sandbox", "game")
        or relative.suffix != ".py"
    ):
        raise ValueError(
            "대상은 sandbox/파일.py 또는 game/파일.py여야 합니다."
        )

    if relative.parts[0] == "sandbox":
        directory = SANDBOX
    else:
        directory, _ = game_location()

    target = directory / relative.name
    test = directory / (test_module + ".py")
    if target == test or target.name.startswith("test_"):
        raise ValueError("테스트 파일을 수정 대상으로 지정할 수 없습니다.")

    check_directory(directory)
    for path in (target, test):
        if path.is_symlink():
            raise ValueError(
                "대상 파일과 테스트에 심볼릭 링크를 사용할 수 없습니다."
            )
    if not target.is_file() or not test.is_file():
        raise ValueError("수정 대상과 고정 테스트 파일이 필요합니다.")
    if target.resolve().parent != directory.resolve():
        raise ValueError("수정 대상이 허용 폴더 밖에 있습니다.")
    if test.resolve().parent != directory.resolve():
        raise ValueError("테스트가 허용 폴더 밖에 있습니다.")

    return target, test


def check_git_files(target, test):
    # ツールの配置場所ではなく、編集対象のGitリポジトリを検査する。
    root = Path(
        git_output(target.parent, "rev-parse", "--show-toplevel")
    ).resolve()

    for path in (target, test):
        relative = path.resolve().relative_to(root).as_posix()
        git_output(root, "ls-files", "--error-unmatch", "--", relative)
        status = git_output(
            root, "status", "--porcelain=v1",
            "--untracked-files=all", "--", relative,
        )
        if status:
            raise RuntimeError(
                f"対象または固定テストにGit変更があります: {relative}"
            )


def prepare_edit(target_file, request, test_module):
    if not isinstance(request, str) or not request.strip():
        raise ValueError("編集依頼が必要です。")
    if len(request) > 4000:
        raise ValueError("編集依頼は4000文字以内にしてください。")
    target, test = resolve_files(target_file, test_module)
    check_git_files(target, test)
    return target, test


def run_test(log_path, test_module="test_clamp", work_dir=None):
    directory = SANDBOX if work_dir is None else Path(work_dir)
    check_directory(directory)
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
        f"type=bind,source={directory.resolve()},target=/work,readonly",
        "--workdir", "/work",
        "python:3.11-slim",
        "python", "-B", "-m", "unittest", "-v", test_module,
    ]
    try:
        with log_path.open("w", encoding="utf-8") as log:
            result = subprocess.run(
                command, stdout=log, stderr=subprocess.STDOUT, timeout=30,
            )
        feedback = log_path.read_text(encoding="utf-8")[-6000:]
        return result.returncode == 0, feedback
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["docker", "rm", "-f", name],
            capture_output=True, timeout=10,
        )
        raise RuntimeError("테스트가 30초를 초과해 중단됐습니다.")


def run_edit(target_file, request, test_module, model=None):
    context = read_context()
    target, test = prepare_edit(target_file, request, test_module)
    model = ask_model if model is None else model
    lock = BASE_DIR / ".edit_loop.lock"
    try:
        lock.open("x").close()
    except FileExistsError:
        raise RuntimeError(
            "실행 중이거나 이전 실행이 중단됐습니다. "
            ".edit_loop.lock을 확인하세요."
        )

    try:
        target, test = prepare_edit(target_file, request, test_module)
        original = target.read_bytes()
        fixed_test = test.read_bytes()
        current = original
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output = BASE_DIR / "outputs" / f"edit_{stamp}"
        output.mkdir(parents=True)
        (output / "original.py").write_bytes(original)

        def finish(status, **details):
            result = {
                "status": status,
                "output": str(output.relative_to(BASE_DIR)),
                **details,
            }
            (output / "result.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return result

        def check_unchanged():
            resolved_target, resolved_test = resolve_files(
                target_file, test_module
            )
            if resolved_target != target or resolved_test != test:
                raise RuntimeError("대상 또는 테스트 경로가 변경됐습니다.")
            if target.read_bytes() != current:
                raise RuntimeError("수정 대상이 외부에서 변경됐습니다.")
            if test.read_bytes() != fixed_test:
                raise RuntimeError("고정 테스트가 변경됐습니다.")
            if read_context() != context:
                raise RuntimeError("브랜치 또는 작업 문맥이 변경됐습니다.")

        feedback = "아직 검사하지 않았습니다."
        for attempt in range(1, MAX_ATTEMPTS + 1):
            check_unchanged()
            prompt = (
                context
                + "\n\n# 수정 요청\n" + request
                + "\n\n파일·네트워크·프로세스 접근은 필요하지 않습니다.\n"
                "실제로 수정하거나 테스트했다고 주장하지 마세요.\n"
                "고정 테스트를 변경하는 대신 지정된 함수를 구현하세요.\n"
                "응답은 Markdown 없이 JSON 객체 하나만 출력하세요.\n"
                '구현할 수 있으면 {"action":"edit","code":"전체 Python 코드"}\n'
                '사용자 결정이 필요하면 {"action":"question",'
                '"question":"한국어 질문"}\n'
                "\n현재 코드:\n" + current.decode("utf-8")
                + "\n이전 검사 결과:\n" + feedback
            )
            print(f"AI 수정 시도 {attempt}/{MAX_ATTEMPTS}", flush=True)
            answer = model(prompt)
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("AI 응답이 비어 있습니다.")
            (output / f"answer_{attempt}.txt").write_text(
                answer, encoding="utf-8"
            )
            check_unchanged()

            try:
                proposal = json.loads(answer)
                if not isinstance(proposal, dict):
                    raise ValueError("JSON 객체가 필요합니다.")
                if proposal.get("action") == "question":
                    question = proposal.get("question")
                    if not isinstance(question, str) or not question.strip():
                        raise ValueError("질문이 비어 있습니다.")
                    check_unchanged()
                    if current != original:
                        target.write_bytes(original)
                        current = original
                    check_unchanged()
                    check_git_files(target, test)
                    return finish(
                        "waiting_for_user",
                        question=question, attempts=attempt,
                    )
                if proposal.get("action") != "edit":
                    raise ValueError("action은 edit 또는 question이어야 합니다.")
                code = proposal.get("code")
                if not isinstance(code, str) or not code.strip():
                    raise ValueError("코드가 비어 있습니다.")
                compile(code, str(target), "exec")
            except (ValueError, SyntaxError) as error:
                feedback = f"응답 형식 또는 문법 오류: {error}"
                print(feedback)
                continue

            candidate = (code.rstrip() + "\n").encode("utf-8")
            (output / f"candidate_{attempt}.py").write_bytes(candidate)
            check_unchanged()
            target.write_bytes(candidate)
            current = candidate

            if Path(target_file).parts[0] == "sandbox":
                passed, feedback = run_test(
                    output / f"test_{attempt}.txt", test_module
                )
            else:
                passed, feedback = run_test(
                    output / f"test_{attempt}.txt",
                    test_module, work_dir=target.parent,
                )
            check_unchanged()
            print(feedback)
            if passed:
                return finish("tests_passed", attempts=attempt)

        return finish(
            "failed",
            error="3회 시도 안에 지정 테스트를 통과하지 못했습니다.",
            attempts=MAX_ATTEMPTS,
        )
    finally:
        lock.unlink()


def main():
    result = run_edit("sandbox/clamp.py", DEFAULT_REQUEST, "test_clamp")
    print("결과:", result["status"])
    if result.get("question"):
        print("확인 필요:", result["question"])
    if result.get("error"):
        print("원인:", result["error"])
    print("기록 위치:", result["output"])


if __name__ == "__main__":
    main()