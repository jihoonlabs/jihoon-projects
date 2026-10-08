import ast
import json
from pathlib import Path

from read_context import CONFIG_PATH
import thumby_capabilities

SUPPORTED_PROFILES = {"thumby"}
THUMBY_ALLOWED_ROOTS = {"buttonL", "buttonR", "display"}
THUMBY_ALLOWED_DISPLAY = {"fill", "drawFilledRectangle", "drawText", "update", "setFPS"}


def current_profile(config_path=None):
    path = Path(CONFIG_PATH if config_path is None else config_path)
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("생성 프로필 설정은 JSON 객체여야 합니다.")
    thumby_capabilities.selected(config)
    profile = config.get("generation_profile")
    if profile is None:
        return None
    if profile not in SUPPORTED_PROFILES:
        raise ValueError("지원하지 않는 생성 프로필입니다: " + str(profile))
    return profile


def design_prompt(area):
    if area != "game" or current_profile() != "thumby":
        return ""
    inputs = ("buttonL/buttonR/buttonU/buttonD/buttonA/buttonB" if "controls" in
              thumby_capabilities.selected(_config()) else "buttonL/buttonR")
    return thumby_capabilities.prompt(_config()) + (
        "\n# 일반 Thumby 생성 계약\n"
        "게임 규칙과 기기 입출력·표시 어댑터를 서로 다른 모듈로 분리하세요. "
        "게임 규칙 모듈은 thumby를 import하지 않고 CPython에서 검사 가능해야 합니다. "
        "실행 대상은 Thumby MicroPython이므로 CPython 전용 모듈·기능에 의존하지 마세요. "
        "게임 폴더와 같은 이름의 엔트리 파일이 기기 어댑터 역할을 함께 맡고, "
        f"그 엔트리 파일만 import thumby를 사용하세요. {inputs} 입력과 "
        "display.fill, drawFilledRectangle, drawText, update, setFPS를 필요한 범위에서 사용하세요. "
        "실기에서 실행할 엔트리 Python 파일은 게임 폴더와 정확히 같은 이름으로 설계하세요. "
        "실제 무한 진입 함수와 별도로 CPython 테스트에서 한 번 호출하고 끝나는 유한 adapter/helper 함수를 설계하고, "
        "CPython 테스트 import에서는 게임 루프를 시작하지 마세요. "
        "일반 Thumby 런처는 엔트리 모듈을 import하므로 엔트리 파일은 "
        "sys.implementation.name == 'micropython'일 때 진입 함수를 호출해 게임을 시작하세요. "
        "런처 요구의 fixed check는 CPython import가 루프를 시작하지 않는 동작으로 표현하고, "
        "MicroPython runtime guard 자체는 구현 단계 generation profile 정적 검사가 담당합니다. "
        "Thumby Color API와 추측한 API는 사용하지 마세요. "
    )


def _entry_filename(directory=None):
    if directory is None:
        config = json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))
        directory = config.get("edit_directory")
        if not isinstance(directory, str) or not directory.strip():
            raise ValueError("일반 Thumby 게임 경로 설정이 필요합니다.")
    return Path(directory).name + ".py"


def _config():
    return json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))


def design_structure(area, directory, requirements):
    if area != "game" or current_profile() != "thumby":
        return ""
    entry = _entry_filename(directory)
    ids = ["R" + str(number) for number in range(1, len(requirements) + 1)]
    example = {"files": [
        {"id": "001", "filename": "rules.py", "functions": [
            {"name": "update_state", "parameters": ["state", "inputs"],
             "behavior": "예시: 전달받은 상태와 입력만으로 다음 상태를 반환. 실제 계약으로 교체."}],
         "checks": [{"requirement": "R1", "case": "실제 입력", "expected": "구체적 반환 상태"}],
         "depends_on": []},
        {"id": "002", "filename": entry, "functions": [
            {"name": "main_loop", "parameters": [],
             "behavior": "MicroPython 가드에서 시작하며 실제 게임 루프를 실행."},
            {"name": "step_frame", "parameters": ["state"],
             "behavior": "유한 프레임 함수. 버튼 읽기→규칙 호출→화면 표시→새 상태 반환."}],
         "checks": [{"requirement": "R1", "case": "fake 기기와 한 프레임 입력", "expected": "상태와 기기 호출"}],
         "depends_on": ["001"]},
    ]}
    return (
        "\n# 실제 대상에 맞는 필수 설계 구조\n"
        f"현재 게임 폴더는 {Path(directory).name}이며 엔트리는 정확히 {entry}입니다. "
        "앞의 module.py 단일 파일은 JSON 필드 예시일 뿐입니다. 실제 답변은 반드시 "
        f"{entry}와 별도의 순수 규칙 파일을 모두 포함하세요. 필요하면 규칙 파일을 더 나눌 수 있습니다. "
        "아래 함수명도 형식 예시이며 승인 명세에 맞는 실제 함수 계약을 작성하세요. "
        "순수 규칙 함수에는 state와 필요한 입력을 명시적으로 전달하고 반환 상태를 정의하세요. "
        "숨겨진 변경 가능한 전역 상태에 의존하지 마세요. 순수 규칙은 기기 저장·읽기·표시를 하지 않습니다. "
        f"실제 saveData I/O와 버튼·화면 호출은 {entry}의 유한 helper에 두고 "
        "저장 값 인코딩·검증은 필요시 순수 함수로 분리하세요. "
        "구매·장착 등 승인 명세에서 분리한 행동을 임의로 합치지 마세요. "
        "files 전체 checks의 requirement가 다음 모든 ID를 포함해야 합니다: "
        + json.dumps(ids) + ". 각 ID의 원문 계약을 확인하고 구체적인 입력·기대 결과로 검사하세요. "
        "응답은 전체 files JSON이며 엔트리와 의존 파일을 생략하지 마세요.\n"
        + json.dumps(example, ensure_ascii=False, separators=(",", ":")) + "\n"
    )


def validate_design(area, files, directory):
    if area != "game" or current_profile() != "thumby":
        return
    entry = _entry_filename(directory)
    entry_item = next((item for item in files if item.get("filename") == entry), None)
    if entry_item is None:
        raise ValueError("일반 Thumby 게임은 폴더명과 같은 엔트리 Python 파일이 필요합니다.")

    pure_ids = {
        item.get("id") for item in files
        if item.get("filename") != entry and isinstance(item.get("id"), str)
    }
    if not pure_ids:
        raise ValueError("일반 Thumby 게임은 엔트리와 분리된 순수 규칙 모듈이 필요합니다.")
    functions = entry_item.get("functions")
    if not isinstance(functions, list) or len(functions) < 2:
        raise ValueError(
            "일반 Thumby 엔트리는 무한 진입 함수와 별도의 유한 adapter/helper 함수가 필요합니다."
        )

    dependencies = entry_item.get("depends_on")
    if (
        not isinstance(dependencies, list)
        or not any(identifier in pure_ids for identifier in dependencies)
    ):
        raise ValueError("일반 Thumby 엔트리는 순수 규칙 모듈에 의존해야 합니다.")


def _sets_fake_thumby(node):
    if isinstance(node, ast.Assign):
        targets = node.targets
    else:
        targets = []
    for target in targets:
        if (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Attribute)
            and isinstance(target.value.value, ast.Name)
            and target.value.value.id == "sys"
            and target.value.attr == "modules"
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == "thumby"
            and not (
                isinstance(node.value, ast.Constant)
                and node.value.value is None
            )
        ):
            return True
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return False
    call = node.value
    return (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "setdefault"
        and isinstance(call.func.value, ast.Attribute)
        and isinstance(call.func.value.value, ast.Name)
        and call.func.value.value.id == "sys"
        and call.func.value.attr == "modules"
        and len(call.args) >= 2
        and isinstance(call.args[0], ast.Constant)
        and call.args[0].value == "thumby"
        and not (
            isinstance(call.args[1], ast.Constant)
            and call.args[1].value is None
        )
    )


def validate_tests(area, candidate, design, directory=None):
    if area != "game" or current_profile() != "thumby":
        return
    entry = _entry_filename(directory)
    entry_source = next(
        (item for item in design["files"] if item.get("filename") == entry), None
    )
    if entry_source is None:
        raise ValueError("일반 Thumby 엔트리 설계가 없습니다.")
    entry_test = next(
        (item for item in candidate["files"] if item.get("id") == entry_source["id"]),
        None,
    )
    if entry_test is None:
        raise ValueError("일반 Thumby 엔트리 테스트가 없습니다.")

    module = Path(entry).stem
    tree = ast.parse(entry_test["code"])
    import_index = next(
        (
            index for index, node in enumerate(tree.body)
            if (
                isinstance(node, ast.Import)
                and any(alias.name == module for alias in node.names)
            ) or (
                isinstance(node, ast.ImportFrom)
                and node.level == 0
                and node.module == module
            )
        ),
        None,
    )
    fake_index = next(
        (index for index, node in enumerate(tree.body) if _sets_fake_thumby(node)),
        None,
    )
    sys_index = next(
        (
            index for index, node in enumerate(tree.body)
            if isinstance(node, ast.Import)
            and any(alias.name == "sys" and alias.asname is None for alias in node.names)
        ),
        None,
    )
    if (
        import_index is None
        or fake_index is None
        or sys_index is None
        or not sys_index < fake_index < import_index
    ):
        raise ValueError(
            "일반 Thumby 엔트리 테스트는 import sys 후 대상 모듈 import 전에 "
            "sys.modules에 가짜 thumby를 주입해야 합니다."
        )


def test_prompt(area):
    if area != "game" or current_profile() != "thumby":
        return ""
    extended = bool(thumby_capabilities.selected(_config()))
    prefix = ("\n기기 모킹 틀을 대상 import보다 앞에 두세요. 각 테스트에서 Mock을 초기화하고 "
              "승인 설계의 유한 helper를 호출하여 버튼·상태 반환·화면 호출을 검사하세요. "
              "저장 테스트는 성공·없음·손상·실패를 fake로 구성하고 실제 파일·기기를 사용하지 마세요.\n"
              + thumby_capabilities.fake_prefix(_config())) if extended else ""
    return prefix + (
        "\n# 일반 Thumby 테스트 계약\n"
        "순수 게임 규칙은 실제 thumby 모듈 없이 검사하세요. "
        "폴더명 엔트리의 기기 어댑터 테스트는 import sys 후 대상 모듈 import 전에 "
        "sys.modules['thumby']에 None이 아닌 가짜 thumby 객체를 직접 주입해 CPython에서 검사 가능하게 하세요. "
        "아래 틀에 제시되는 대상 모듈 import 문장은 유지하되, 그 import보다 앞에 sys import와 fake 주입 코드를 삽입하세요. "
        + ("이동·공격·메뉴·장착·저장 중 승인 설계에 있는 조건을 checks에 따라 검사하세요. " if extended else
           "좌우 이동 경계·장애물 충돌·점수·재시작 조건을 설계 checks에 따라 직접 assertion으로 확인하세요. ")
        + "승인 설계의 functions에 없는 새 production 함수·클래스·상수 계약을 테스트에서 만들지 마세요. "
        "CPython 테스트에서 엔트리를 import해도 게임 루프가 시작되지 않는 구조를 유지하고, "
        "실제 무한 진입 함수를 테스트에서 직접 호출하지 말고 import 안전성과 유한 helper 동작을 검사하세요. "
        "런처/runtime guard 관련 check는 CPython import-safe 동작을 assertion하고, "
        "MicroPython guard의 존재 자체를 unittest에서 실행해 증명하려 하지 마세요. "
    )


def implementation_prompt(area, filename):
    if area != "game" or current_profile() != "thumby":
        return ""
    entry = _entry_filename()
    if filename == entry:
        game_name = Path(entry).stem
        role = (
            "이 파일은 폴더명 엔트리이자 기기 어댑터입니다. 공식 일반 Thumby API만 사용하세요. "
            f"MicroPython에서 sibling 규칙 모듈을 import하기 전에 sys.path에 /Games/{game_name}을 추가하세요. "
            "이 기기 경로 추가는 MicroPython 조건 안에서만 수행해 CPython import의 sys.path는 바꾸지 마세요. "
            "CPython import에서는 게임 루프를 시작하지 말고, "
            "sys.implementation.name == 'micropython'일 때 승인 설계에서 런타임 진입 역할인 함수를 직접 호출해 "
            "Thumby 런처 import에서 실제 게임을 시작하세요. 유한 adapter/helper만 한 번 호출하고 끝내면 안 됩니다. "
        )
    else:
        role = (
            "이 파일은 순수 게임 규칙 모듈입니다. thumby를 import하거나 기기 경로를 설정하지 마세요. "
        )
    return (
        "\n# 일반 Thumby 구현 계약\n"
        "승인 설계의 역할 분리를 유지하세요. "
        + role
        + (thumby_capabilities.prompt(_config()) if filename == entry else "")
        + "Thumby MicroPython에서 실행할 수 있도록 CPython 전용 모듈·기능을 사용하지 마세요. "
        + f"현재 구현 대상은 {filename} 하나뿐입니다. "
    )


def _is_micropython_guard(test):
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq):
        return False

    def implementation_name(node):
        return (
            isinstance(node, ast.Attribute)
            and node.attr == "name"
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "implementation"
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "sys"
        )

    left, right = test.left, test.comparators[0]
    return (
        implementation_name(left)
        and isinstance(right, ast.Constant)
        and right.value == "micropython"
    ) or (
        implementation_name(right)
        and isinstance(left, ast.Constant)
        and left.value == "micropython"
    )


def _validate_entry_start(tree):
    defined = {
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    sys_import = any(
        isinstance(node, ast.Import)
        and any(alias.name == "sys" and alias.asname is None for alias in node.names)
        for node in tree.body
    )
    guards = [
        node for node in tree.body
        if isinstance(node, ast.If) and _is_micropython_guard(node.test)
    ]
    start_names = {
        statement.value.func.id
        for node in guards
        for statement in node.body
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id in defined
        )
    }
    if not sys_import or not start_names:
        raise ValueError(
            "일반 Thumby 엔트리는 import sys 후 "
            "sys.implementation.name == 'micropython' 조건에서 "
            "정의한 진입 함수를 호출해야 합니다."
        )

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        # else/elif는 CPython import에서도 실행될 수 있다.
        candidates = node.orelse if node in guards else [node]
        if any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id in start_names
            for statement in candidates
            for child in ast.walk(statement)
        ):
            raise ValueError(
                "일반 Thumby 진입 함수는 MicroPython guard 밖 최상위에서 호출할 수 없습니다."
            )


def validate_code(area, code, filename=None):
    if area != "game" or current_profile() != "thumby":
        return
    tree = ast.parse(code)
    allowed = thumby_capabilities.allowed(_config())
    entry_filename = _entry_filename() if filename is not None else None
    if filename is not None and filename == entry_filename:
        _validate_entry_start(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [item.name for item in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        if any(name == "thumbyColor" or name.startswith("thumbyColor.") for name in names):
            raise ValueError("일반 Thumby 생성에서 Thumby Color 모듈을 사용할 수 없습니다.")
        if (
            filename is not None
            and filename != entry_filename
            and any(name == "thumby" or name.startswith("thumby.") for name in names)
        ):
            raise ValueError("일반 Thumby에서는 폴더명 엔트리 파일만 thumby를 import할 수 있습니다.")
        if isinstance(node, ast.Import):
            for item in node.names:
                if item.name == "thumby" and item.asname is not None:
                    raise ValueError("일반 Thumby는 import thumby 형태로 사용해야 합니다.")
                if item.name.startswith("thumby."):
                    raise ValueError("확인하지 않은 일반 Thumby 하위 모듈을 사용할 수 없습니다.")
        elif node.module == "thumby" or (node.module or "").startswith("thumby."):
            raise ValueError("일반 Thumby는 import thumby 형태로 사용해야 합니다.")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        chain = []
        current = node
        while isinstance(current, ast.Attribute):
            chain.append(current.attr)
            current = current.value
        if not isinstance(current, ast.Name) or current.id != "thumby":
            continue
        chain.reverse()
        if not chain or chain[0] not in allowed:
            raise ValueError("확인하지 않은 일반 Thumby API를 사용할 수 없습니다.")
        if len(chain) > 2 or (len(chain) == 2 and chain[1] not in allowed[chain[0]]):
            raise ValueError("확인하지 않은 Thumby " + chain[0] + " API를 사용할 수 없습니다.")

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        statements = node.orelse if isinstance(node, ast.If) and _is_micropython_guard(node.test) else [node]
        for statement in statements:
            for child in ast.walk(statement):
                if (isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                        and isinstance(child.func.value, ast.Attribute)
                        and isinstance(child.func.value.value, ast.Name)
                        and child.func.value.value.id == "thumby"
                        and child.func.value.attr == "saveData"):
                    raise ValueError("CPython import 경로의 최상위 저장 I/O는 사용할 수 없습니다.")

    for node in tree.body:
        if isinstance(node, ast.While) and isinstance(node.test, ast.Constant) and node.test.value is True:
            raise ValueError("모듈 최상위의 무한 루프는 사용할 수 없습니다.")
