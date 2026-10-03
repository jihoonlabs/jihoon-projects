import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import edit_loop


def resolve_create_files(target_file, test_module):
    if not isinstance(target_file, str) or not target_file.strip():
        raise ValueError("생성 대상 경로가 필요합니다.")
    if (
        not isinstance(test_module, str)
        or not test_module.isidentifier()
        or not test_module.startswith("test_")
    ):
        raise ValueError("테스트 모듈은 test_로 시작하는 Python 식별자여야 합니다.")

    relative = Path(target_file)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or len(relative.parts) != 2
        or relative.parts[0] not in ("sandbox", "game")
        or relative.suffix != ".py"
    ):
        raise ValueError("대상은 sandbox/파일.py 또는 game/파일.py여야 합니다.")

    if relative.parts[0] == "sandbox":
        directory = edit_loop.SANDBOX
    else:
        directory, _ = edit_loop.game_location()

    edit_loop.check_directory(directory)
    target = directory / relative.name
    test = directory / (test_module + ".py")

    if target == test or target.name.startswith("test_"):
        raise ValueError("테스트 파일을 생성 대상으로 지정할 수 없습니다.")
    if target.is_symlink() or test.is_symlink():
        raise ValueError("대상과 테스트에 심볼릭 링크를 사용할 수 없습니다.")
    if not test.is_file():
        raise ValueError("고정 테스트 파일이 필요합니다.")
    if test.resolve().parent != directory.resolve():
        raise ValueError("테스트가 허용 폴더 밖에 있습니다.")

    return target, test


def prepare_create(target_file, request, test_module):
    if not isinstance(request, str) or not request.strip():
        raise ValueError("생성 요청이 필요합니다.")
    if len(request) > 4000:
        raise ValueError("생성 요청은 4000자 이내여야 합니다.")

    target, test = resolve_create_files(target_file, test_module)
    if target.exists() or target.is_symlink():
        raise ValueError("생성 대상이 이미 존재합니다.")

    # 固定テストだけを既存のGit検査へ通す。
    edit_loop.check_git_files(test, test)
    root = Path(
        edit_loop.git_output(target.parent, "rev-parse", "--show-toplevel")
    ).resolve()
    relative = target.resolve().relative_to(root).as_posix()

    # 削除済みの追跡ファイルも新規作成の対象にしない。
    tracked = edit_loop.git_output(root, "ls-files", "--", relative)
    status = edit_loop.git_output(
        root, "status", "--porcelain=v1",
        "--untracked-files=all", "--", relative,
    )
    if tracked or status:
        raise RuntimeError("생성 대상에 Git 기록 또는 기존 변경이 있습니다.")

    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", relative],
        cwd=root, capture_output=True, text=True, timeout=10,
    )
    if ignored.returncode == 0:
        raise ValueError("Git에서 제외한 파일은 생성 대상으로 사용할 수 없습니다.")
    if ignored.returncode != 1:
        raise RuntimeError("생성 대상의 Git 제외 여부를 확인하지 못했습니다.")

    return target, test


def run_create(target_file, request, test_module, model=None):
    context = edit_loop.read_context()
    target, test = prepare_create(target_file, request, test_module)
    model = edit_loop.ask_model if model is None else model

    # editとcreateは同じロックを使う。
    lock = edit_loop.BASE_DIR / ".edit_loop.lock"
    try:
        lock.open("x").close()
    except FileExistsError:
        raise RuntimeError(
            "수정 또는 생성 작업이 실행 중이거나 이전 실행이 중단됐습니다."
        )

    output = None
    current = None
    identity = None

    try:
        target, test = prepare_create(target_file, request, test_module)
        fixed_test = test.read_bytes()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output = edit_loop.BASE_DIR / "outputs" / f"create_{stamp}"
        output.mkdir(parents=True)
        (output / "request.txt").write_text(request, encoding="utf-8")

        def finish(status, **details):
            result = {
                "status": status,
                "output": str(output.relative_to(edit_loop.BASE_DIR)),
                **details,
            }
            (output / "result.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return result

        def check_unchanged():
            resolved_target, resolved_test = resolve_create_files(
                target_file, test_module
            )
            if resolved_target != target or resolved_test != test:
                raise RuntimeError("생성 대상 또는 테스트 경로가 변경됐습니다.")
            if test.read_bytes() != fixed_test:
                raise RuntimeError("고정 테스트가 외부에서 변경됐습니다.")
            edit_loop.check_git_files(test, test)
            if edit_loop.read_context() != context:
                raise RuntimeError("브랜치 또는 작업 문맥이 변경됐습니다.")

            if current is None:
                if target.exists() or target.is_symlink():
                    raise RuntimeError("생성 대상이 외부에서 만들어졌습니다.")
            else:
                if not target.is_file() or target.is_symlink():
                    raise RuntimeError("생성 파일의 종류가 외부에서 변경됐습니다.")
                stat = target.stat()
                if (stat.st_dev, stat.st_ino) != identity:
                    raise RuntimeError("생성 파일이 외부에서 교체됐습니다.")
                if target.read_bytes() != current:
                    raise RuntimeError("생성 파일이 외부에서 변경됐습니다.")

        def remove_created():
            nonlocal current, identity
            check_unchanged()
            if current is not None:
                target.unlink()
                current = None
                identity = None
            check_unchanged()

        def write_candidate(candidate):
            nonlocal current, identity
            check_unchanged()
            if current is None:
                # 初回は排他的に作成し、既存ファイルを上書きしない。
                with target.open("xb") as stream:
                    stat = os.fstat(stream.fileno())
                    identity = (stat.st_dev, stat.st_ino)
                    current = b""
                    stream.write(candidate)
                    stream.flush()
                    current = candidate
            else:
                # オープン後も同じファイル・内容であることを確認する。
                descriptor = os.open(
                    target, os.O_RDWR | os.O_NOFOLLOW
                )
                with os.fdopen(descriptor, "r+b") as stream:
                    stat = os.fstat(stream.fileno())
                    if (stat.st_dev, stat.st_ino) != identity:
                        raise RuntimeError("生成ファイルが外部で置換されました。")
                    if stream.read() != current:
                        raise RuntimeError("生成ファイルが外部で変更されました。")
                    stream.seek(0)
                    stream.write(candidate)
                    stream.truncate()
                    stream.flush()
                    current = candidate
            check_unchanged()

        feedback = "아직 검사하지 않았습니다."
        attempts = 0

        try:
            for attempt in range(1, edit_loop.MAX_ATTEMPTS + 1):
                attempts = attempt
                check_unchanged()
                prompt = (
                    context
                    + "\n\n# 새 파일 생성 요청\n" + request
                    + "\n\n생성 대상: " + target_file
                    + "\n파일·네트워크·프로세스 접근은 필요하지 않습니다.\n"
                    "실제로 파일을 생성하거나 검사했다고 주장하지 마세요.\n"
                    "고정 테스트는 변경할 수 없습니다.\n"
                    "응답은 Markdown 없이 JSON 객체 하나로 출력하세요.\n"
                    '구현: {"action":"create","code":"전체 Python 코드"}\n'
                    '결정 필요: {"action":"question","question":"한국어 질문"}\n'
                    "\n현재 후보 코드:\n"
                    + (current.decode("utf-8") if current is not None else "(없음)")
                    + "\n이전 검사 결과:\n" + feedback
                )
                print(
                    f"AI 생성 시도 {attempt}/{edit_loop.MAX_ATTEMPTS}",
                    flush=True,
                )
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
                        remove_created()
                        return finish(
                            "waiting_for_user",
                            question=question, attempts=attempt,
                        )
                    if proposal.get("action") != "create":
                        raise ValueError("action은 create 또는 question이어야 합니다.")
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
                write_candidate(candidate)
                passed, feedback = edit_loop.run_test(
                    output / f"test_{attempt}.txt",
                    test_module, work_dir=target.parent,
                )
                check_unchanged()
                print(feedback)
                if passed:
                    return finish("tests_passed", attempts=attempt)

            remove_created()
            return finish(
                "failed",
                error="3회 시도 안에 지정 테스트를 통과하지 못했습니다.",
                attempts=attempts,
            )
        except Exception as error:
            # 外部変更があれば削除せず、停止理由を記録する。
            try:
                remove_created()
            except Exception as cleanup_error:
                finish(
                    "failed",
                    error=str(error),
                    cleanup_error=str(cleanup_error),
                    attempts=attempts,
                )
            else:
                finish("failed", error=str(error), attempts=attempts)
            raise
    finally:
        lock.unlink()