import ast
import json
from pathlib import Path

from read_context import CONFIG_PATH

SUPPORTED_PROFILES = {"thumby"}
THUMBY_ALLOWED_ROOTS = {"buttonL", "buttonR", "display"}
THUMBY_ALLOWED_DISPLAY = {"fill", "drawFilledRectangle", "drawText", "update", "setFPS"}


def current_profile(config_path=None):
    path = Path(CONFIG_PATH if config_path is None else config_path)
    config = json.loads(path.read_text(encoding="utf-8"))
    profile = config.get("generation_profile")
    if profile is None:
        return None
    if profile not in SUPPORTED_PROFILES:
        raise ValueError("지원하지 않는 생성 프로필입니다: " + str(profile))
    return profile


def design_prompt(area):
    if area != "game" or current_profile() != "thumby":
        return ""
    return (
        "\n# 일반 Thumby 생성 계약\n"
        "게임 규칙과 기기 입출력·표시 어댑터를 서로 다른 모듈로 분리하세요. "
        "게임 규칙 모듈은 thumby를 import하지 않고 CPython에서 검사 가능해야 합니다. "
        "실행 대상은 Thumby MicroPython이므로 CPython 전용 모듈·기능에 의존하지 마세요. "
        "기기 어댑터만 import thumby를 사용하며 buttonL/buttonR 입력과 "
        "display.fill, drawFilledRectangle, drawText, update, setFPS를 필요한 범위에서 사용하세요. "
        "실기에서 실행할 엔트리 Python 파일은 게임 폴더와 정확히 같은 이름으로 설계하세요. "
        "실제 진입 함수를 분리하고 CPython 테스트 import에서는 게임 루프를 시작하지 마세요. "
        "일반 Thumby 런처는 엔트리 모듈을 import하므로 엔트리 파일은 "
        "sys.implementation.name == 'micropython'일 때 진입 함수를 호출해 게임을 시작하세요. "
        "Thumby Color API와 추측한 API는 사용하지 마세요. "
    )


def _entry_filename(directory=None):
    if directory is None:
        config = json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))
        directory = config.get("edit_directory")
        if not isinstance(directory, str) or not directory.strip():
            raise ValueError("일반 Thumby 게임 경로 설정이 필요합니다.")
    return Path(directory).name + ".py"


def validate_design(area, files, directory):
    if area != "game" or current_profile() != "thumby":
        return
    entry = _entry_filename(directory)
    if not any(item.get("filename") == entry for item in files):
        raise ValueError("일반 Thumby 게임은 폴더명과 같은 엔트리 Python 파일이 필요합니다.")


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
        and bool(call.args)
        and isinstance(call.args[0], ast.Constant)
        and call.args[0].value == "thumby"
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
    return (
        "\n# 일반 Thumby 테스트 계약\n"
        "순수 게임 규칙은 실제 thumby 모듈 없이 검사하세요. "
        "기기 어댑터 테스트가 thumby를 필요로 하면 import 전에 sys.modules에 "
        "가짜 thumby를 주입하거나 unittest.mock으로 대체해 CPython에서 검사 가능하게 하세요. "
        "좌우 이동 경계·장애물 충돌·점수·재시작 조건을 설계 checks에 따라 직접 assertion으로 확인하세요. "
        "어댑터 import가 무한 루프를 시작하지 않는 구조를 유지하세요. "
    )


def implementation_prompt(area, filename):
    if area != "game" or current_profile() != "thumby":
        return ""
    return (
        "\n# 일반 Thumby 구현 계약\n"
        "승인 설계의 역할 분리를 유지하세요. 규칙 모듈에는 thumby 의존성을 넣지 말고, "
        "기기 어댑터에서만 공식 일반 Thumby API를 사용하세요. "
        "Thumby MicroPython에서 실행할 수 있도록 CPython 전용 모듈·기능을 사용하지 마세요. "
        "CPython import에서는 게임 루프를 시작하지 마세요. 엔트리 파일은 "
        "sys.implementation.name == 'micropython'일 때 진입 함수를 호출해 "
        "Thumby 런처 import에서 실제 게임을 시작하세요. "
        f"현재 구현 대상은 {filename} 하나뿐입니다. "
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
    guarded_start = any(
        isinstance(node, ast.If)
        and _is_micropython_guard(node.test)
        and any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id in defined
            for statement in node.body
            for child in ast.walk(statement)
        )
        for node in tree.body
    )
    if not sys_import or not guarded_start:
        raise ValueError(
            "일반 Thumby 엔트리는 import sys 후 "
            "sys.implementation.name == 'micropython' 조건에서 "
            "정의한 진입 함수를 호출해야 합니다."
        )


def validate_code(area, code, filename=None):
    if area != "game" or current_profile() != "thumby":
        return
    tree = ast.parse(code)
    if filename == _entry_filename():
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
        if not chain or chain[0] not in THUMBY_ALLOWED_ROOTS:
            raise ValueError("확인하지 않은 일반 Thumby API를 사용할 수 없습니다.")
        if (
            chain[0] == "display"
            and len(chain) >= 2
            and chain[1] not in THUMBY_ALLOWED_DISPLAY
        ):
            raise ValueError("확인하지 않은 Thumby display API를 사용할 수 없습니다.")
        if (
            chain[0] in {"buttonL", "buttonR"}
            and len(chain) >= 2
            and chain[1] != "pressed"
        ):
            raise ValueError("확인하지 않은 Thumby button API를 사용할 수 없습니다.")

    for node in tree.body:
        if isinstance(node, ast.While) and isinstance(node.test, ast.Constant) and node.test.value is True:
            raise ValueError("모듈 최상위의 무한 루프는 사용할 수 없습니다.")
