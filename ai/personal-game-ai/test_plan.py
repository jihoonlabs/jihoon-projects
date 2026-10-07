import argparse
import ast
import hashlib
import json
from datetime import datetime
from pathlib import Path

import design_plan
import generation_profile
from ask_ai import ask_model
from read_context import read_context

BASE_DIR = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_approved_design(path):
    source, data, envelope = design_plan.read_design(path)
    approval = source.with_name("approval.json")
    if approval.is_symlink():
        raise ValueError("승인 기록에 심볼릭 링크를 사용할 수 없습니다.")
    approval_data = approval.read_bytes()
    record = json.loads(approval_data)
    if (
        not isinstance(record, dict)
        or record.get("design_sha256") != digest(data)
        or not isinstance(record.get("approved_at"), str)
        or not record["approved_at"].strip()
    ):
        raise ValueError("현재 설계 버전의 승인 기록이 필요합니다.")
    if source.read_bytes() != data or approval.read_bytes() != approval_data:
        raise RuntimeError("읽는 중 설계 또는 승인 기록이 변경됐습니다.")
    return source, data, approval_data, envelope


def validate_code(code, module, check_count):
    if not isinstance(code, str) or not code.strip() or len(code) > 20000:
        raise ValueError("테스트 코드는 1~20000자여야 합니다.")
    try:
        tree = ast.parse(code)
        compile(tree, "<test-candidate>", "exec")
    except (SyntaxError, ValueError) as error:
        raise ValueError(f"Python 구문 오류: {error}") from error

    # This is a structure check, not a security boundary.
    unittest_imported = any(
        isinstance(node, ast.Import)
        and any(alias.name == "unittest" and alias.asname is None
                for alias in node.names)
        for node in tree.body
    )
    module_imported = any(
        (
            isinstance(node, ast.Import)
            and any(alias.name == module for alias in node.names)
        )
        or (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module == module
        )
        for node in tree.body
    )
    if not unittest_imported or not module_imported:
        raise ValueError("unittest와 설계 대상 모듈을 직접 import해야 합니다.")

    methods = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(
            isinstance(base, ast.Attribute)
            and isinstance(base.value, ast.Name)
            and base.value.id == "unittest"
            and base.attr == "TestCase"
            for base in node.bases
        ):
            continue
        if node.decorator_list:
            raise ValueError("테스트 클래스에 데코레이터를 사용할 수 없습니다.")
        for method in node.body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not method.name.startswith("test_"):
                continue
            if (
                isinstance(method, ast.AsyncFunctionDef)
                or method.decorator_list
                or len(method.args.args) != 1
                or method.args.args[0].arg != "self"
                or method.args.posonlyargs
                or method.args.kwonlyargs
                or method.args.vararg
                or method.args.kwarg
                or method.args.defaults
            ):
                raise ValueError("테스트는 데코레이터 없는 test_*(self)여야 합니다.")
            if method.name in methods:
                raise ValueError("테스트 메서드 이름은 파일 안에서 고유해야 합니다.")
            if not any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id == "self"
                and child.func.attr.startswith("assert")
                for child in ast.walk(method)
            ):
                raise ValueError("각 테스트 메서드에 unittest assertion이 필요합니다.")
            methods[method.name] = method

    if not check_count <= len(methods) <= 64:
        raise ValueError("검사 사례 수 이상의 테스트 메서드가 필요합니다.")
    return set(methods)


def validate_candidate(proposal, design):
    if not isinstance(proposal, dict) or set(proposal) != {"files"}:
        raise ValueError("files만 포함한 JSON 객체가 필요합니다.")
    files = proposal["files"]
    expected = {item["id"]: item for item in design["files"]}
    if not isinstance(files, list) or len(files) != len(expected):
        raise ValueError("설계 파일마다 테스트 파일 하나가 필요합니다.")

    result = {}
    for item in files:
        if not isinstance(item, dict) or set(item) != {
            "id", "filename", "code", "covers"
        }:
            raise ValueError("테스트 후보 필드가 잘못됐습니다.")
        identifier = item["id"]
        if (
            not isinstance(identifier, str)
            or identifier not in expected
            or identifier in result
        ):
            raise ValueError("설계 파일 ID가 잘못됐거나 중복됐습니다.")
        source = expected[identifier]
        module = Path(source["filename"]).stem
        if item["filename"] != f"test_{module}.py":
            raise ValueError("테스트 파일명은 test_<설계 모듈명>.py여야 합니다.")

        methods = validate_code(item["code"], module, len(source["checks"]))
        covers = item["covers"]
        if not isinstance(covers, list) or len(covers) != len(source["checks"]):
            raise ValueError("모든 설계 검사 사례에 메서드 연결이 필요합니다.")
        indexes = set()
        linked = set()
        for cover in covers:
            if not isinstance(cover, dict) or set(cover) != {
                "check", "method"
            }:
                raise ValueError("검사 연결 필드가 잘못됐습니다.")
            index = cover["check"]
            method = cover["method"]
            if (
                type(index) is not int
                or not 1 <= index <= len(source["checks"])
                or index in indexes
                or not isinstance(method, str)
                or method not in methods
                or method in linked
            ):
                raise ValueError("검사 번호와 테스트 메서드는 각각 고유해야 합니다.")
            indexes.add(index)
            linked.add(method)
        result[identifier] = {
            **item,
            "code": item["code"].rstrip() + "\n",
        }
    return {"files": [result[item["id"]] for item in design["files"]]}


def generate_tests(path, model=None):
    context = read_context()
    source, source_data, approval_data, envelope = read_approved_design(path)
    model = ask_model if model is None else model

    def check_unchanged():
        if read_context() != context:
            raise RuntimeError("작업 문맥이 변경됐습니다.")
        current, data, approval, _ = read_approved_design(source)
        if (
            current != source
            or data != source_data
            or approval != approval_data
        ):
            raise RuntimeError("설계 또는 승인 기록이 변경됐습니다.")

    check_unchanged()
    output = BASE_DIR / "outputs"
    if output.is_symlink():
        raise ValueError("outputs에 심볼릭 링크를 사용할 수 없습니다.")
    output.mkdir(exist_ok=True)
    folder = output / (
        "test_plan_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    folder.mkdir()
    write_json(folder / "request.json", {
        "source": str(source.relative_to(BASE_DIR)),
        "source_sha256": digest(source_data),
        "request": envelope["request"],
        "design": envelope["design"],
        "context": context,
    })
    feedback = "아직 검사하지 않았습니다."

    for attempt in range(1, 4):
        check_unchanged()
        prompt = (
            context
            + "\n\n# 승인한 설계\n"
            + json.dumps({
                "request": envelope["request"],
                "design": envelope["design"],
            }, ensure_ascii=False)
            + "\nPython 표준 unittest로 테스트 후보를 작성하세요. "
            "구현 코드는 작성하지 마세요. "
            "import unittest와 설계 대상 모듈의 직접 import를 사용하세요. "
            "클래스는 unittest.TestCase를 직접 상속하세요. "
            "검사 사례마다 고유한 test_ 메서드 하나와 assertion을 작성하세요. "
            "구현 파일이 아직 없어도 테스트 후보를 작성할 수 있습니다. "
            "mock 검사도 생략하지 말고 unittest.mock의 patch를 사용하세요. "
            "대상 모듈이 참조하는 함수 이름을 patch하세요. "
            "예: with patch('물약모듈.heal', return_value=7) as mocked: "
            "안에서 result = use_potion(5, 10, 2)를 호출하고 "
            "mocked.assert_called_once_with(5, 4, 10)과 "
            "self.assertEqual(result, (7, 1))을 모두 작성하세요. "
            "예시의 모듈명과 값은 실제 설계 검사 조건에 맞추세요. "
            "heal 재사용은 두 모듈을 import하고 "
            "self.assertIs(물약모듈.heal, 회복모듈.heal)로 확인하세요. "
            "pass나 설명만으로 검사를 대체하지 마세요. "
            "검사 번호는 각 설계 파일 checks의 1부터 시작하는 순서입니다. "
            "건너뛰기 데코레이터를 사용하지 마세요. "
            "기대값은 설계 계약에서 정하고 구현 결과로 계산하지 마세요. "
            "파일·네트워크·프로세스 접근은 필요하지 않습니다. "
            "파일을 만들거나 테스트를 실행했다고 주장하지 마세요. "
            "Markdown 없이 JSON만 반환하세요:\n"
            "설계 파일마다 별도 테스트 파일 하나를 반환하세요. "
            "여러 모듈의 테스트를 한 파일에 합치지 마세요. "
            "테스트 안에 설계 함수나 구현 코드를 정의하지 마세요. "
            + generation_profile.test_prompt(envelope["request"]["area"])
            + "아래 code에 제시한 import를 유지하고 실제 대상 함수를 검사하세요. "
            "아래 틀의 id·filename·검사 번호를 그대로 유지하세요. "
            "code에는 해당 모듈의 전체 테스트 코드를 넣고 "
            "covers의 method에는 실제 메서드 이름을 넣으세요. "
            "응답 첫 문자는 {, 마지막 문자는 }여야 합니다. "
            "백틱·설명·Markdown 코드 블록을 붙이지 마세요.\n"
            + json.dumps({
                "files": [
                    {
                        "id": item["id"],
                        "filename": "test_" + item["filename"],
                        "code": (
                            "import unittest\nfrom "
                            + Path(item["filename"]).stem
                            + " import "
                            + ", ".join(
                                function["name"]
                                for function in item["functions"]
                            )
                            + "\n\n"
                            + "# 이 import를 유지하고 unittest.TestCase와 "
                            + "검사 메서드를 작성하세요. 구현 함수는 작성 금지."
                        ),
                        "covers": [
                            {"check": number, "method": f"test_case_{number}"}
                            for number in range(1, len(item["checks"]) + 1)
                        ],
                    }
                    for item in envelope["design"]["files"]
                ]
            }, ensure_ascii=False)
            + "\n"
            "# 이전 구조 검사\n" + feedback
        )
        print(f"AI 테스트 제안 시도 {attempt}/3", flush=True)
        answer = model(prompt)
        check_unchanged()
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("AI 응답이 비어 있습니다.")
        (folder / f"answer_{attempt}.txt").write_text(answer, encoding="utf-8")
        try:
            if len(answer) > 100000:
                raise ValueError("응답이 100000자를 넘습니다.")
            candidate = validate_candidate(
                json.loads(answer), envelope["design"]
            )
            generation_profile.validate_tests(
                envelope["request"]["area"], candidate, envelope["design"]
            )
        except ValueError as error:
            feedback = str(error)
            print("테스트 구조 검사 실패:", feedback)
            continue

        check_unchanged()
        result = {
            "source": str(source.relative_to(BASE_DIR)),
            "source_sha256": digest(source_data),
            "approval_sha256": digest(approval_data),
            "context": context,
            "tests": candidate,
        }
        # Store candidates as text so unittest discovery cannot execute them.
        for item in candidate["files"]:
            with (folder / (item["filename"] + ".txt")).open(
                "x", encoding="utf-8"
            ) as stream:
                stream.write(item["code"])
        manifest = folder / "tests.json"
        write_json(manifest, result)
        print("테스트 후보 SHA-256:", digest(manifest.read_bytes()))
        return manifest

    raise RuntimeError(f"테스트 후보 생성 실패. 기록: {folder}")


def confirm_tests(path, expected_digest):
    path = Path(path).absolute()
    if (
        path.name != "tests.json"
        or path.parent.parent != BASE_DIR / "outputs"
        or not path.parent.name.startswith("test_plan_")
    ):
        raise ValueError("outputs/test_plan_*/tests.json만 확정할 수 있습니다.")
    for candidate in (BASE_DIR, path.parent.parent, path.parent, path):
        if candidate.is_symlink():
            raise ValueError("후보 경로에 심볼릭 링크를 사용할 수 없습니다.")

    data = path.read_bytes()
    if digest(data) != expected_digest:
        raise RuntimeError("검토한 테스트 후보 버전과 다릅니다.")
    record = json.loads(data)
    if not isinstance(record, dict) or set(record) != {
        "source", "source_sha256", "approval_sha256", "context", "tests"
    }:
        raise ValueError("테스트 후보 저장 형식이 잘못됐습니다.")
    relative = record["source"]
    if not isinstance(relative, str):
        raise ValueError("원본 설계 경로가 필요합니다.")
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("원본 설계는 도구 내부 상대 경로여야 합니다.")
    source, source_data, approval_data, envelope = read_approved_design(
        BASE_DIR / relative
    )
    if (
        record["source_sha256"] != digest(source_data)
        or record["approval_sha256"] != digest(approval_data)
        or record["context"] != read_context()
    ):
        raise RuntimeError("원본 설계·승인 기록·문맥이 변경됐습니다.")
    candidate = validate_candidate(record["tests"], envelope["design"])
    for item in candidate["files"]:
        copy = path.parent / (item["filename"] + ".txt")
        if copy.is_symlink() or copy.read_bytes() != item["code"].encode("utf-8"):
            raise RuntimeError("표시용 테스트 후보가 변경됐습니다.")
    if (
        path.read_bytes() != data
        or source.read_bytes() != source_data
        or source.with_name("approval.json").read_bytes() != approval_data
        or read_context() != record["context"]
    ):
        raise RuntimeError("확정 중 입력이 변경됐습니다.")
    confirmation = path.with_name("confirmation.json")
    write_json(confirmation, {
        "tests_sha256": expected_digest,
        "source_sha256": record["source_sha256"],
        "confirmed_at": datetime.now().isoformat(),
    })
    return confirmation


def main():
    parser = argparse.ArgumentParser(description="설계 기반 테스트 후보 준비")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--design", type=Path)
    group.add_argument("--confirm", type=Path)
    parser.add_argument("--sha256")
    args = parser.parse_args()
    if args.confirm:
        if not args.sha256:
            parser.error("--confirm에는 --sha256이 필요합니다.")
        print("확정 기록:", confirm_tests(args.confirm, args.sha256))
    else:
        if args.sha256:
            parser.error("--sha256은 확정에만 사용합니다.")
        print("테스트 후보 저장:", generate_tests(args.design))


if __name__ == "__main__":
    main()
