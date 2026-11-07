import ast
import json
from pathlib import Path

from read_context import CONFIG_PATH

BASE_DIR = Path(__file__).resolve().parent
PLATFORM_DIR = BASE_DIR / "platforms"
SUPPORTED = ("thumby",)

# 元祖ThumbyのMicroPythonで使う想定のモジュールだけを許可する。
# 一覧外でも実機で動く場合はあるが、確認できるまで生成コードには使わせない。
THUMBY_IMPORTS = frozenset((
    "thumby", "time", "utime", "random", "urandom", "math", "gc",
    "micropython", "machine", "sys", "struct", "ustruct", "framebuf",
    "array", "json", "ujson",
))

# MicroPythonが対応しない構文。ホスト側Pythonの版にない型は無視する。
_UNSUPPORTED = tuple(
    node for node in (
        getattr(ast, "Match", None),
        getattr(ast, "TryStar", None),
        getattr(ast, "TypeAlias", None),
    ) if node is not None
)

THUMBY_NOTE = (
    "\n\n# 대상 기기: 원래 Thumby\n"
    "- MicroPython에서 실행됩니다. 화면은 72x40 흑백(색 0 또는 1)입니다.\n"
    "- 기본 글꼴은 5x7이고 글자 사이 간격은 1입니다.\n"
    "- import는 " + ", ".join(sorted(THUMBY_IMPORTS))
    + "와 같은 폴더의 모듈만 사용합니다.\n"
    "- 화면·입력·소리·저장은 thumby.display, thumby.buttonA/B/U/D/L/R,"
    " thumby.audio, thumby.saveData를 사용합니다.\n"
    "- match 문, except*, 상대 import, CPython 전용 모듈은 사용하지 않습니다.\n"
    "- 화면 밖에 그리지 않습니다.\n"
)


def configured_platform(config_path=CONFIG_PATH):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("설정은 JSON 객체여야 합니다.")
    value = config.get("platform")
    if value is None:
        return None
    if value not in SUPPORTED:
        raise ValueError(
            "platform은 " + ", ".join(SUPPORTED) + " 중 하나여야 합니다."
        )
    edit_directory = config.get("edit_directory")
    if not isinstance(edit_directory, str) or not edit_directory.strip():
        raise ValueError("platform은 edit_directory와 함께 지정해야 합니다.")
    return value


def target_platform(target_file):
    # sandboxは汎用検査のまま残し、ゲームフォルダだけに機種を適用する。
    if Path(target_file).parts[0] == "sandbox":
        return None
    return configured_platform()


def prompt_note(platform):
    if platform is None:
        return ""
    if platform == "thumby":
        return THUMBY_NOTE
    raise ValueError("지원하지 않는 platform입니다.")


def docker_options(platform):
    if platform is None:
        return []
    if platform != "thumby":
        raise ValueError("지원하지 않는 platform입니다.")
    source = (PLATFORM_DIR / "thumby").resolve()
    if not (source / "thumby.py").is_file():
        raise RuntimeError("검사용 thumby 모듈이 없습니다.")
    return [
        "--mount", f"type=bind,source={source},target=/platform,readonly",
        "--env", "PYTHONPATH=/platform",
    ]


def check_thumby_source(path, local_modules):
    """生成コードを実行せず、構文木だけで互換性を確認する。"""
    path = Path(path)
    errors = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
    except (SyntaxError, UnicodeDecodeError) as error:
        return [f"{path.name}: 문법 오류: {error}"]

    allowed = THUMBY_IMPORTS | set(local_modules)
    for node in ast.walk(tree):
        line = getattr(node, "lineno", "?")
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in allowed:
                    errors.append(
                        f"{path.name}:{line}: Thumby에서 허용하지 않는 import: "
                        f"{alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                errors.append(
                    f"{path.name}:{line}: 상대 import는 사용할 수 없습니다."
                )
                continue
            top = (node.module or "").split(".")[0]
            if top not in allowed:
                errors.append(
                    f"{path.name}:{line}: Thumby에서 허용하지 않는 import: "
                    f"{node.module}"
                )
        elif _UNSUPPORTED and isinstance(node, _UNSUPPORTED):
            errors.append(
                f"{path.name}:{line}: MicroPython 미지원 문법: "
                f"{type(node).__name__}"
            )
    return errors


def check_directory_source(platform, directory):
    """テスト以外のゲームファイルを検査し、問題の一覧を返す。"""
    if platform is None:
        return []
    if platform != "thumby":
        raise ValueError("지원하지 않는 platform입니다.")
    directory = Path(directory)
    files = sorted(
        path for path in directory.glob("*.py")
        if not path.name.startswith("test_")
    )
    local_modules = {path.stem for path in files}
    errors = []
    for path in files:
        if path.is_symlink():
            errors.append(f"{path.name}: 심볼릭 링크는 검사하지 않습니다.")
            continue
        errors.extend(check_thumby_source(path, local_modules))
    return errors
