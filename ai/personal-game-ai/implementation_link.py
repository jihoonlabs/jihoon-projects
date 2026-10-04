import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

import design_plan
import edit_loop
import plan_tasks
import test_plan

BASE_DIR = Path(__file__).resolve().parent


def read_confirmed(path, expected_digest):
    path = Path(path).absolute()
    if (
        path.name != "tests.json"
        or path.parent.parent != BASE_DIR / "outputs"
        or not path.parent.name.startswith("test_plan_")
    ):
        raise ValueError("outputs/test_plan_*/tests.json만 사용할 수 있습니다.")

    for item in (BASE_DIR, path.parent.parent, path.parent, path):
        if item.is_symlink():
            raise ValueError("후보 경로에 심볼릭 링크를 사용할 수 없습니다.")

    data = path.read_bytes()
    if test_plan.digest(data) != expected_digest:
        raise RuntimeError("검토한 테스트 후보 SHA-256과 다릅니다.")

    record = json.loads(data)
    if not isinstance(record, dict) or set(record) != {
        "source", "source_sha256", "approval_sha256", "context", "tests"
    }:
        raise ValueError("테스트 후보 저장 형식이 잘못됐습니다.")

    confirmation = path.with_name("confirmation.json")
    if confirmation.is_symlink():
        raise ValueError("확정 기록에 심볼릭 링크를 사용할 수 없습니다.")
    confirmation_data = confirmation.read_bytes()
    confirmed = json.loads(confirmation_data)
    if (
        not isinstance(confirmed, dict)
        or set(confirmed) != {
            "tests_sha256", "source_sha256", "confirmed_at"
        }
        or confirmed["tests_sha256"] != expected_digest
        or confirmed["source_sha256"] != record["source_sha256"]
        or not isinstance(confirmed["confirmed_at"], str)
        or not confirmed["confirmed_at"].strip()
    ):
        raise ValueError("현재 후보 버전의 확정 기록이 필요합니다.")

    relative = record["source"]
    if not isinstance(relative, str):
        raise ValueError("원본 설계 경로가 필요합니다.")
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("설계는 도구 내부 상대 경로여야 합니다.")

    source, source_data, approval_data, envelope = (
        test_plan.read_approved_design(BASE_DIR / relative)
    )
    if (
        record["source_sha256"] != test_plan.digest(source_data)
        or record["approval_sha256"] != test_plan.digest(approval_data)
        or record["context"] != edit_loop.read_context()
    ):
        raise RuntimeError("설계·승인·현재 문맥이 후보 기록과 다릅니다.")

    candidate = test_plan.validate_candidate(
        record["tests"], envelope["design"]
    )
    copies = []
    for item in candidate["files"]:
        copy = path.parent / (item["filename"] + ".txt")
        code = item["code"].encode("utf-8")
        if copy.is_symlink() or copy.read_bytes() != code:
            raise RuntimeError("표시용 테스트 후보가 변경됐습니다.")
        copies.append((copy, code))

    snapshot = (
        data, confirmation_data, source_data, approval_data, record["context"]
    )
    if (
        path.read_bytes() != data
        or confirmation.read_bytes() != confirmation_data
        or source.read_bytes() != source_data
        or source.with_name("approval.json").read_bytes() != approval_data
        or edit_loop.read_context() != record["context"]
        or any(
            copy.is_symlink() or copy.read_bytes() != code
            for copy, code in copies
        )
    ):
        raise RuntimeError("읽는 중 입력이 변경됐습니다.")

    return envelope, candidate, snapshot


def check_unused(path):
    root = Path(
        edit_loop.git_output(path.parent, "rev-parse", "--show-toplevel")
    ).resolve()
    relative = path.relative_to(root).as_posix()
    if path.exists() or path.is_symlink():
        raise ValueError(f"기존 파일을 덮어쓸 수 없습니다: {path.name}")
    if edit_loop.git_output(root, "ls-files", "--", relative):
        raise ValueError(f"Git 추적 파일을 설치 대상으로 사용할 수 없습니다: {path.name}")
    if edit_loop.git_output(
        root, "status", "--porcelain=v1",
        "--untracked-files=all", "--", relative,
    ):
        raise RuntimeError(f"설치 경로에 기존 Git 변경이 있습니다: {path.name}")

    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", relative],
        cwd=root, capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        raise ValueError(f"Git에서 제외한 경로에는 설치할 수 없습니다: {path.name}")
    if result.returncode != 1:
        raise RuntimeError("Git 제외 여부를 확인하지 못했습니다.")


def install_tests(path, expected_digest):
    lock = edit_loop.BASE_DIR / ".edit_loop.lock"
    try:
        with lock.open("x"):
            pass
    except FileExistsError:
        raise RuntimeError("파일 작업이 실행 중이거나 이전 실행이 중단됐습니다.")

    created = []
    try:
        envelope, candidate, snapshot = read_confirmed(path, expected_digest)
        directory = design_plan.directory_for(envelope["request"]["area"])
        files = [
            (directory / item["filename"], item["code"].encode("utf-8"))
            for item in candidate["files"]
        ]
        for destination, _ in files:
            check_unused(destination)

        def check_inputs():
            current_envelope, current_candidate, current = read_confirmed(
                path, expected_digest
            )
            if (
                current != snapshot
                or current_envelope != envelope
                or current_candidate != candidate
                or design_plan.directory_for(
                    envelope["request"]["area"]
                ) != directory
            ):
                raise RuntimeError("설치 중 입력 또는 작업 영역이 변경됐습니다.")
            for installed, code in created:
                if installed.is_symlink() or installed.read_bytes() != code:
                    raise RuntimeError("설치 파일이 외부에서 변경됐습니다.")

        for destination, code in files:
            check_inputs()
            check_unused(destination)
            # 배타적으로 생성하여 기존 파일을 덮어쓰지 않는다.
            with destination.open("xb") as stream:
                stream.write(code)
            created.append((destination, code))
            check_inputs()

        return [destination for destination, _ in created]
    except Exception as error:
        # 외부 파일을 삭제하지 않는다. 부분 설치는 사람이 확인한다.
        if created:
            names = ", ".join(str(path) for path, _ in created)
            raise RuntimeError(
                f"설치가 중단됐습니다. 생성 파일을 보존했습니다: {names}. "
                f"원인: {error}"
            ) from error
        raise
    finally:
        lock.unlink()


def build_tasks(envelope, candidate):
    request = envelope["request"]
    area = request["area"]
    directory = design_plan.directory_for(area)
    tests = {item["id"]: item for item in candidate["files"]}
    allowed = []
    proposals = []

    for item in envelope["design"]["files"]:
        fixed = tests[item["id"]]
        installed = directory / fixed["filename"]
        if (
            installed.is_symlink()
            or not installed.is_file()
            or installed.read_bytes() != fixed["code"].encode("utf-8")
        ):
            raise RuntimeError(
                f"설치한 테스트가 확정 후보와 다릅니다: {fixed['filename']}"
            )
        edit_loop.check_git_files(installed, installed)
        contract = {
            "kind": "create",
            "target": f"{area}/{item['filename']}",
            "test_module": Path(fixed["filename"]).stem,
        }
        allowed.append(contract)
        detail = {
            "requirements": request["requirements"],
            "functions": item["functions"],
            "checks": item["checks"],
            "dependencies": [
                {
                    "id": dependency,
                    "filename": next(
                        source["filename"]
                        for source in envelope["design"]["files"]
                        if source["id"] == dependency
                    ),
                }
                for dependency in item["depends_on"]
            ],
        }
        proposals.append({
            **contract,
            "id": item["id"],
            "depends_on": list(item["depends_on"]),
            "prompt": (
                "아래 승인 설계의 함수 계약과 검사 조건을 구현하세요.\n"
                "전체 목표 중 이번 target 파일만 구현하세요.\n"
                "최상위 함수는 아래 functions에 지정된 것만 정의하세요.\n"
                "다른 작업의 함수를 이 파일에 추가하거나 복제하지 마세요.\n"
                "선행 함수는 dependencies의 filename에서 import하여 사용하세요.\n"
                "전달된 선행 코드는 참고 자료이며 복사할 구현 코드가 아닙니다.\n"
                + json.dumps(detail, ensure_ascii=False)
            ),
        })

    return plan_tasks.validate_plan(
        {"tasks": proposals}, allowed, request["goal"]
    )


def create_plan(path, expected_digest):
    envelope, candidate, snapshot = read_confirmed(path, expected_digest)
    tasks = build_tasks(envelope, candidate)

    output = BASE_DIR / "outputs"
    if output.is_symlink():
        raise ValueError("outputs에 심볼릭 링크를 사용할 수 없습니다.")
    folder = output / (
        "plan_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    folder.mkdir()
    test_plan.write_json(folder / "request.json", {
        "source_tests": str(Path(path).absolute().relative_to(BASE_DIR)),
        "tests_sha256": expected_digest,
        "goal": envelope["request"]["goal"],
        "origin": "confirmed_design",
    })

    current_envelope, current_candidate, current = read_confirmed(
        path, expected_digest
    )
    if (
        current != snapshot
        or current_envelope != envelope
        or current_candidate != candidate
        or build_tasks(current_envelope, current_candidate) != tasks
    ):
        raise RuntimeError("계획 저장 전 입력 또는 설치 파일이 변경됐습니다.")

    destination = folder / "tasks.json"
    test_plan.write_json(destination, tasks)
    return destination


def main():
    parser = argparse.ArgumentParser(description="확정 테스트 설치·구현 계획 연결")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install", type=Path)
    group.add_argument("--plan", type=Path)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()

    if args.install:
        for path in install_tests(args.install, args.sha256):
            print("설치:", path)
        print("테스트 실행 없음. 내용 검토 후 Git commit이 필요합니다.")
    else:
        print("계획 저장:", create_plan(args.plan, args.sha256))
        print("구현은 아직 실행하지 않았습니다.")


if __name__ == "__main__":
    main()