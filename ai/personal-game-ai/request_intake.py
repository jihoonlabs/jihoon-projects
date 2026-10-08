"""Offline request preparation; does not run the generation workflow."""

import argparse
import json

QUESTIONS = {
    "play": "주인공이 하는 핵심 행동과 조작을 정해주세요. 예: 좌우 이동으로 장애물 피하기.",
    "finish": "성공·실패·재시작 조건을 정해주세요. 예: 충돌하면 종료하고 양쪽 버튼으로 재시작.",
}


def prepare(brief, settings=None):
    if not isinstance(brief, str) or not brief.strip() or len(brief) > 3000:
        raise ValueError("게임 요청은 1~3000자여야 합니다.")
    settings = {} if settings is None else settings
    if not isinstance(settings, dict) or set(settings) - set(QUESTIONS):
        raise ValueError("설정에는 play·finish만 사용할 수 있습니다.")
    for key, value in settings.items():
        if not isinstance(value, str) or not value.strip() or len(value) > 400:
            raise ValueError(key + " 설정은 1~400자여야 합니다.")
    missing = [{"id": key, "question": question} for key, question in QUESTIONS.items() if key not in settings]
    result = {
        "stage": "needs_settings" if missing else "request_ready",
        "brief": brief, "settings": dict(settings), "questions": missing,
        "request": None,
        "limitations": [
            "원문의 의미를 자동 추론하지 않습니다. 이미 정한 내용은 설정으로 전달하세요.",
            "현재 Thumby 프로필은 좌우 버튼과 제한된 표시 API용입니다. 액션 게임 등 새 조작은 설계 범위를 먼저 확인하세요.",
            "request_ready는 구현 가능성 검증이나 게임 완성을 뜻하지 않습니다.",
        ],
    }
    if not missing:
        result["request"] = {
            "goal": "일반 Thumby 게임 요청: " + brief,
            "requirements": [
                "핵심 플레이: " + settings["play"],
                "성공·실패·재시작: " + settings["finish"],
                "시나리오와 분위기는 목표의 사용자 원문을 따르고, 불명확한 취향·범위 결정만 사용자에게 확인한다.",
                "게임 규칙은 순수 Python 모듈로, 기기 입출력은 별도 어댑터로 구현한다.",
                "일반 Thumby MicroPython과 현재 생성 프로필의 허용 API를 사용하고 CPython import에서는 게임 루프를 시작하지 않는다.",
            ],
            "area": "game",
        }
    return result


def main():
    parser = argparse.ArgumentParser(description="Ollama 없이 게임 요청과 필요한 사용자 설정 정리")
    parser.add_argument("--brief", required=True)
    parser.add_argument("--play")
    parser.add_argument("--finish")
    parser.add_argument("--request-only", action="store_true", help="설정이 완성된 경우 workflow 요청 JSON만 출력")
    args = parser.parse_args()
    try:
        result = prepare(args.brief, {key: value for key, value in {"play": args.play, "finish": args.finish}.items() if value is not None})
        if args.request_only and result["request"] is None:
            raise ValueError("play·finish 설정을 먼저 채우세요. --request-only 없이 필요한 질문을 확인하세요.")
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result["request"] if args.request_only else result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
