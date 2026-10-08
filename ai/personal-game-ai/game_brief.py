"""Collect a device-specific product brief without claiming research or approval."""

import argparse
import json
from pathlib import Path


DEVICES = {
    "thumby": "일반 Thumby",
    "thumby-color": "Thumby Color",
}
FIELDS = {
    "genre": "만들고 싶은 장르·플레이 형식을 정해주세요.",
    "experience": "살리고 싶은 핵심 재미를 설명해주세요.",
}


def prepare(device, settings=None):
    if device not in DEVICES:
        raise ValueError("기기는 thumby 또는 thumby-color여야 합니다.")
    settings = {} if settings is None else settings
    if not isinstance(settings, dict) or set(settings) - set(FIELDS):
        raise ValueError("설정에는 genre·experience만 사용할 수 있습니다.")
    for key, value in settings.items():
        if not isinstance(value, str) or not value.strip() or len(value) > 1000:
            raise ValueError(key + "는 1~1000자여야 합니다.")
    questions = [{"id": key, "question": question} for key, question in FIELDS.items() if key not in settings]
    return {
        "schema_version": 1,
        "stage": "needs_settings" if questions else "needs_research",
        "device": {"id": device, "name": DEVICES[device]},
        "settings": dict(settings),
        "questions": questions,
        "policy": {
            "original_expression_only": True,
            "copy_source_game": False,
            "similarity_goal": "장르·플레이 형식·핵심 재미를 기기 제약 안에서 최대한 살린다.",
        },
        "research": {"gameplay": [], "hardware": []},
        "feasibility": "not_assessed",
        "specification_approved": False,
        "next": "누락 설정을 입력하세요." if questions else "게임 형식·기기 자료 조사 후 축소안과 명세를 제시하세요.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="장르·기기 입력을 조사 전 기획 파일로 저장")
    parser.add_argument("--device", choices=DEVICES, required=True)
    parser.add_argument("--genre")
    parser.add_argument("--experience")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        settings = {key: value for key, value in vars(args).items() if key in FIELDS and value is not None}
        result = prepare(args.device, settings)
        if args.interactive:
            for question in result["questions"]:
                settings[question["id"]] = input(question["question"] + "\n")
                prepare(args.device, settings)
            result = prepare(args.device, settings)
        if args.output is not None:
            if result["questions"]:
                raise ValueError("설정이 빠져 기획 파일을 저장할 수 없습니다.")
            # This is a planning dossier, never a workflow request or approval.
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, EOFError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
