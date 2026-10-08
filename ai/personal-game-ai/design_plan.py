import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import edit_loop
import generation_profile
from ask_ai import ask_model
from read_context import read_context
from task_dependencies import order_tasks

BASE_DIR = Path(__file__).resolve().parent


def directory_for(area):
    if area == "sandbox":
        directory = edit_loop.SANDBOX
    elif area == "game":
        directory, _ = edit_loop.game_location()
    else:
        raise ValueError("영역은 sandbox 또는 game이어야 합니다.")
    edit_loop.check_directory(directory)
    return directory


def validate_input(goal, requirements, area):
    if not isinstance(goal, str) or not goal.strip() or len(goal) > 4000:
        raise ValueError("목표는 1~4000자의 문자열이어야 합니다.")
    if (
        not isinstance(requirements, list)
        or not 1 <= len(requirements) <= 12
        or not all(
            isinstance(value, str) and value.strip() and len(value) <= 500
            for value in requirements
        )
        or len(set(requirements)) != len(requirements)
    ):
        raise ValueError("고유한 필수 조건 1~12개가 필요합니다.")
    return directory_for(area)


def validate_design(proposal, requirements, area):
    if not isinstance(proposal, dict) or set(proposal) != {"files"}:
        raise ValueError("files만 포함한 JSON 객체가 필요합니다.")
    files = proposal["files"]
    if not isinstance(files, list) or not 1 <= len(files) <= 8:
        raise ValueError("파일 제안은 1~8개여야 합니다.")

    directory = directory_for(area)
    names = set()
    covered = set()
    required_ids = {f"R{number}" for number in range(1, len(requirements) + 1)}

    for item in files:
        if not isinstance(item, dict) or set(item) != {
            "id", "filename", "functions", "checks", "depends_on"
        }:
            raise ValueError("파일 제안 필드가 잘못됐습니다.")
        filename = item["filename"]
        if not isinstance(filename, str):
            raise ValueError("파일명은 문자열이어야 합니다.")
        relative = Path(filename)
        if (
            len(relative.parts) != 1
            or relative.suffix != ".py"
            or not relative.stem.isidentifier()
            or relative.stem.startswith("test_")
            or filename in names
        ):
            raise ValueError("고유한 Python 모듈 파일명이 필요합니다.")
        target = directory / filename
        if target.exists() or target.is_symlink():
            raise ValueError("이미 존재하는 파일은 제안할 수 없습니다.")
        tracked = edit_loop.git_output(directory, "ls-files", "--", filename)
        if tracked:
            raise ValueError("삭제된 Git 추적 파일도 제안할 수 없습니다.")
        names.add(filename)

        functions = item["functions"]
        if not isinstance(functions, list) or not 1 <= len(functions) <= 8:
            raise ValueError("파일마다 함수 계약 1~8개가 필요합니다.")
        function_names = set()
        for function in functions:
            if not isinstance(function, dict) or set(function) != {
                "name", "parameters", "behavior"
            }:
                raise ValueError("함수 계약 필드가 잘못됐습니다.")
            name = function["name"]
            parameters = function["parameters"]
            behavior = function["behavior"]
            if (
                not isinstance(name, str)
                or not name.isidentifier()
                or name in function_names
            ):
                raise ValueError("고유한 함수 이름이 필요합니다.")
            if (
                not isinstance(parameters, list)
                or not all(
                    isinstance(value, str) and value.isidentifier()
                    for value in parameters
                )
                or len(set(parameters)) != len(parameters)
                or len(parameters) > 12
            ):
                raise ValueError("함수 인자 목록이 잘못됐습니다.")
            if (
                not isinstance(behavior, str)
                or not behavior.strip()
                or len(behavior) > 1500
            ):
                raise ValueError("함수 동작 설명이 필요합니다.")
            function_names.add(name)

        checks = item["checks"]
        if not isinstance(checks, list) or not 1 <= len(checks) <= 16:
            raise ValueError("파일마다 검사 조건 1~16개가 필요합니다.")
        for check in checks:
            if not isinstance(check, dict) or set(check) != {
                "requirement", "case", "expected"
            }:
                raise ValueError("검사 조건 필드가 잘못됐습니다.")
            requirement = check["requirement"]
            if not isinstance(requirement, str) or requirement not in required_ids:
                raise ValueError("검사는 원래 필수 조건 ID를 참조해야 합니다.")
            for key in ("case", "expected"):
                value = check[key]
                if (
                    not isinstance(value, str)
                    or not value.strip()
                    or len(value) > 1000
                ):
                    raise ValueError("검사 입력과 기대 결과가 필요합니다.")
            covered.add(requirement)

    generation_profile.validate_design(area, files, directory)

    if covered != required_ids:
        missing = ", ".join(sorted(required_ids - covered))
        raise ValueError(
            "검사에 연결되지 않은 필수 조건 ID: " + missing
            + ". 해당 조건도 checks의 별도 사례로 작성하세요. "
            "함수 구성 조건은 모듈에 정의된 함수 이름 목록 검사로 표현할 수 있습니다."
        )
    return {"files": order_tasks(files)}


def read_design(path, *, require_current_context=True):
    path = Path(path).absolute()
    if (
        path.name != "design.json"
        or path.parent.parent != BASE_DIR / "outputs"
        or not path.parent.name.startswith("design_")
    ):
        raise ValueError("outputs/design_*/design.json만 사용할 수 있습니다.")
    for candidate in (BASE_DIR, path.parent.parent, path.parent, path):
        if candidate.is_symlink():
            raise ValueError("설계 경로에 심볼릭 링크를 사용할 수 없습니다.")

    data = path.read_bytes()
    envelope = json.loads(data)
    if (
        not isinstance(envelope, dict)
        or not {"request", "design", "context"} <= set(envelope)
        or set(envelope) - {"request", "design", "context", "revision"}
    ):
        raise ValueError("설계 저장 형식이 잘못됐습니다.")
    request = envelope["request"]
    if not isinstance(request, dict) or set(request) != {
        "goal", "requirements", "area"
    }:
        raise ValueError("설계 입력 기록이 잘못됐습니다.")
    requirements = request["requirements"]
    if not isinstance(requirements, dict) or list(requirements) != [
        f"R{number}" for number in range(1, len(requirements) + 1)
    ]:
        raise ValueError("원래 필수 조건 기록이 잘못됐습니다.")
    validate_input(request["goal"], list(requirements.values()), request["area"])
    validate_design(envelope["design"], list(requirements.values()), request["area"])
    if not isinstance(envelope["context"], str) or not envelope["context"].strip():
        raise ValueError("설계 생성 당시 문맥 기록이 필요합니다.")

    # Approval requires the exact context; revision creates a new proposal.
    if require_current_context and envelope["context"] != read_context():
        raise RuntimeError("설계 생성 당시 문맥과 다릅니다.")
    if path.read_bytes() != data:
        raise RuntimeError("읽는 중 설계가 변경됐습니다.")
    return path, data, envelope


def validate_feedback(feedback):
    if (
        not isinstance(feedback, str)
        or not feedback.strip()
        or len(feedback) > 4000
    ):
        raise ValueError("검토 의견은 1~4000자의 문자열이어야 합니다.")


def generate_design(
    goal, requirements, area, model=None, *, previous=None, feedback=None
):
    context = read_context()
    if previous is None:
        if feedback is not None:
            raise ValueError("검토 의견에는 이전 설계가 필요합니다.")
        revision = None
        previous_design = None
    else:
        validate_feedback(feedback)
        source, source_data, envelope = read_design(
            previous, require_current_context=False
        )
        original = envelope["request"]
        if original != {
            "goal": goal,
            "requirements": {
                f"R{number}": value
                for number, value in enumerate(requirements, 1)
            },
            "area": area,
        }:
            raise ValueError("수정 설계는 원래 목표와 필수 조건을 유지해야 합니다.")
        revision = {
            "source": str(source.relative_to(BASE_DIR)),
            "source_sha256": hashlib.sha256(source_data).hexdigest(),
            "feedback": feedback,
        }
        previous_design = envelope["design"]

    directory = validate_input(goal, requirements, area)
    initial_names = sorted(path.name for path in directory.iterdir())
    model = ask_model if model is None else model
    request = {
        "goal": goal,
        "requirements": {
            f"R{number}": value
            for number, value in enumerate(requirements, 1)
        },
        "area": area,
    }

    def check_unchanged():
        if read_context() != context:
            raise RuntimeError("작업 문맥이 변경됐습니다.")
        if validate_input(goal, requirements, area) != directory:
            raise RuntimeError("작업 영역이 변경됐습니다.")
        if sorted(path.name for path in directory.iterdir()) != initial_names:
            raise RuntimeError("작업 영역의 파일 목록이 변경됐습니다.")
        if revision is not None:
            for candidate in (source.parent.parent, source.parent, source):
                if candidate.is_symlink():
                    raise RuntimeError("이전 설계 경로가 변경됐습니다.")
            if source.read_bytes() != source_data:
                raise RuntimeError("이전 설계가 변경됐습니다.")

    check_unchanged()
    output = BASE_DIR / "outputs"
    output.mkdir(exist_ok=True)
    folder = output / (
        "design_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    folder.mkdir()
    with (folder / "request.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(request, ensure_ascii=False, indent=2) + "\n")
    if revision is not None:
        with (folder / "revision.json").open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(revision, ensure_ascii=False, indent=2) + "\n")

    validation_feedback = "아직 검사하지 않았습니다."
    revision_prompt = ""
    if revision is not None:
        revision_prompt = (
            "\n# 이전 설계\n"
            + json.dumps(previous_design, ensure_ascii=False)
            + "\n# 사용자 검토 의견\n"
            + feedback
            + "\n원래 목표·필수 조건·허용 영역은 유지하세요. "
            "검토 의견을 반영해 전체 설계를 다시 반환하세요. "
            "검토 의견이 필수 조건과 충돌하면 필수 조건을 우선하세요. "
            "이전 설계는 검토 자료이며 현재 작업 지침을 따르세요. "
            "기존 승인 여부와 관계없이 새 검토가 필요한 제안입니다.\n"
        )

    for attempt in range(1, 4):
        check_unchanged()
        prompt = (
            context + "\n\n# 설계 입력\n"
            + json.dumps(request, ensure_ascii=False)
            + "\n기존 파일명:\n" + json.dumps(initial_names)
            + generation_profile.design_prompt(area)
            + "\n새 Python 모듈의 파일 구성·함수 계약·검사를 제안하세요. "
            "필수 조건은 변경하지 말고 R1 등의 ID로 검사에 연결하세요. "
            "함수 객체의 필드는 name, parameters, behavior만 허용합니다. "
            "함수 객체에 depends_on 등 추가 필드를 넣지 마세요. "
            "depends_on은 파일 객체에만 두며 다른 파일의 ID만 참조합니다. "
            "함수 호출과 재사용 조건은 behavior에 설명하세요. "
            "기존 파일이나 원작 콘텐츠를 복사하지 마세요. "
            "파일 생성·실행·검사를 수행했다고 주장하지 마세요. "
            "Markdown 없이 다음 형태의 JSON만 반환하세요:\n"
            '{"files":[{"id":"001","filename":"module.py",'
            '"functions":[{"name":"function","parameters":["value"],'
            '"behavior":"동작 설명"}],'
            '"checks":[{"requirement":"R1","case":"검사 입력",'
            '"expected":"기대 결과"}],"depends_on":[]}]}\n'
            + revision_prompt
            + generation_profile.design_structure(area, directory, requirements)
            + "# 이전 구조 검사\n" + validation_feedback
        )
        print(f"AI 설계 시도 {attempt}/3", flush=True)
        answer = model(prompt)
        check_unchanged()
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("AI 응답이 비어 있습니다.")
        (folder / f"answer_{attempt}.txt").write_text(answer, encoding="utf-8")
        try:
            if len(answer) > 30000:
                raise ValueError("설계 응답이 30000자를 넘습니다.")
            design = validate_design(json.loads(answer), requirements, area)
        except ValueError as error:
            validation_feedback = str(error)
            print("설계 검사 실패:", validation_feedback)
            continue

        check_unchanged()
        path = folder / "design.json"
        envelope = {"request": request, "design": design, "context": context}
        if revision is not None:
            envelope["revision"] = revision
        with path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n")
        print("설계 SHA-256:", hashlib.sha256(path.read_bytes()).hexdigest())
        return path

    raise RuntimeError(f"설계 생성 실패. 기록: {folder}")


def revise_design(path, feedback, model=None):
    validate_feedback(feedback)
    source, _, envelope = read_design(path, require_current_context=False)
    request = envelope["request"]
    return generate_design(
        request["goal"],
        list(request["requirements"].values()),
        request["area"],
        model=model,
        previous=source,
        feedback=feedback,
    )


def approve_design(path, expected_digest):
    path, data, _ = read_design(path)
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_digest:
        raise RuntimeError("검토한 설계 버전과 다릅니다.")
    if path.read_bytes() != data:
        raise RuntimeError("승인 중 설계가 변경됐습니다.")
    approval = path.with_name("approval.json")
    with approval.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "design_sha256": actual,
            "approved_at": datetime.now().isoformat(),
        }, indent=2) + "\n")
    return approval


def main():
    parser = argparse.ArgumentParser(description="목표 기반 설계 제안")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--request", type=Path)
    group.add_argument("--revise", type=Path)
    group.add_argument("--approve", type=Path)
    parser.add_argument("--feedback", type=Path)
    parser.add_argument("--sha256")
    args = parser.parse_args()

    if args.approve:
        if not args.sha256:
            parser.error("--approve에는 --sha256이 필요합니다.")
        if args.feedback:
            parser.error("--feedback은 수정 설계에만 사용합니다.")
        print("승인 기록:", approve_design(args.approve, args.sha256))
    elif args.revise:
        if not args.feedback:
            parser.error("--revise에는 --feedback 의견파일이 필요합니다.")
        if args.sha256:
            parser.error("--sha256은 승인에만 사용합니다.")
        feedback = args.feedback.read_text(encoding="utf-8")
        print("수정 설계 저장:", revise_design(args.revise, feedback))
    else:
        if args.sha256 or args.feedback:
            parser.error("--request에는 --sha256·--feedback을 사용하지 않습니다.")
        request = json.loads(args.request.read_text(encoding="utf-8"))
        if not isinstance(request, dict) or set(request) != {
            "goal", "requirements", "area"
        }:
            raise ValueError("입력은 goal·requirements·area를 갖습니다.")
        print("설계 저장:", generate_design(**request))


if __name__ == "__main__":
    main()
