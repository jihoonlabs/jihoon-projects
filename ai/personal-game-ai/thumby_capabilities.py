"""Opt-in, documented monochrome Thumby APIs; no device or model imports."""

FEATURES = {"controls", "save_data"}
DISPLAY = {"fill", "drawFilledRectangle", "drawText", "update", "setFPS"}
SAVE = {"setName", "setItem", "getItem", "hasItem", "save"}


def selected(config):
    value = config.get("thumby_features", [])
    if (not isinstance(value, list) or any(not isinstance(item, str) or item not in FEATURES for item in value)
            or len(value) != len(set(value))):
        raise ValueError("thumby_features는 중복 없는 controls/save_data 목록이어야 합니다.")
    if value and config.get("generation_profile") != "thumby":
        raise ValueError("Thumby 확장 기능은 일반 thumby 프로필에서만 사용할 수 있습니다.")
    return set(value)


def allowed(config):
    features = selected(config)
    methods = {"display": set(DISPLAY), "buttonL": {"pressed"}, "buttonR": {"pressed"}}
    if "controls" in features:
        for button in ("buttonL", "buttonR", "buttonU", "buttonD", "buttonA", "buttonB"):
            methods[button] = {"pressed", "justPressed"}
    if "save_data" in features:
        methods["saveData"] = set(SAVE)
    return methods


def prompt(config):
    features = selected(config)
    text = "\n# 기기 제약\n일반 Thumby는 72x40 흑백 화면입니다. Start 버튼은 없습니다. "
    if "controls" in features:
        text += ("buttonL/R/U/D는 십자키 좌/우/위/아래, buttonA/B는 동작 버튼입니다. "
                 "pressed는 누르고 있는 상태, justPressed는 한 번의 입력에 사용하세요. "
                 "허용 입력은 이 여섯 버튼의 pressed/justPressed뿐입니다. ")
    if "save_data" in features:
        text += ("저장은 saveData.setName/setItem/getItem/hasItem/save만 사용하세요. "
                 "setName에는 게임 폴더명을 사용하고 실제 저장·읽기는 명시된 유한 helper 또는 "
                 "MicroPython 실행 경로에서만 하세요. CPython import 중 저장 I/O 금지. "
                 "값은 문서가 지원하는 스칼라 또는 같은 타입 원소의 목록으로 인코딩하고 "
                 "dict 자체를 저장하지 마세요. 매 프레임 저장하지 마세요. "
                 "저장 없음·손상·실패 처리를 테스트하고 실기 재시작 복구는 미검증으로 남기세요. ")
    return text


def fake_prefix(config):
    methods = allowed(config)
    lines = ["import sys", "import types", "from unittest.mock import Mock",
             "fake_thumby = types.ModuleType('thumby')"]
    for root, names in sorted(methods.items()):
        lines.append("fake_thumby." + root + " = Mock(spec=" + repr(sorted(names)) + ")")
        if root.startswith("button"):
            for name in sorted(names):
                lines.append("fake_thumby." + root + "." + name + ".return_value = False")
    if "saveData" in methods:
        lines.extend(["fake_thumby.saveData.hasItem.return_value = False",
                      "fake_thumby.saveData.getItem.side_effect = KeyError('missing save')"])
    lines.append("sys.modules['thumby'] = fake_thumby")
    return "\n".join(lines) + "\n"
