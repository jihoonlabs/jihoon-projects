"""Attach explicit evidence to a planning brief, without granting approval."""

import argparse
import copy
from datetime import date
import json
from pathlib import Path
from urllib.parse import urlsplit

from game_brief import prepare


def attach(brief, evidence):
    if not isinstance(brief, dict) or brief.get("schema_version") != 1:
        raise ValueError("지원하는 기획 파일이 아닙니다.")
    device = brief.get("device")
    if not isinstance(device, dict):
        raise ValueError("기기 정보가 없습니다.")
    canonical = prepare(device.get("id"), brief.get("settings"))
    if canonical["questions"] or brief.get("policy") != canonical["policy"]:
        raise ValueError("입력과 원본 복사 금지 정책을 먼저 확인하세요.")
    # Research cannot inherit a downstream approval or mutate another device's dossier.
    if brief.get("stage") != "needs_research" or brief.get("specification_approved") is not False:
        raise ValueError("조사 전·명세 미승인 기획만 갱신할 수 있습니다.")
    if not isinstance(evidence, dict) or set(evidence) != {"device", "entries"} or evidence["device"] != device["id"]:
        raise ValueError("조사 자료의 대상 기기가 기획과 다릅니다.")
    entries = evidence["entries"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise ValueError("조사 항목은 1~100개여야 합니다.")
    research = {"gameplay": [], "hardware": []}
    for entry in entries:
        fields = {"category", "topic", "finding", "source", "checked_on", "status"}
        if not isinstance(entry, dict) or set(entry) != fields:
            raise ValueError("조사 항목의 필드가 잘못됐습니다.")
        for key in fields:
            value = entry[key]
            if not isinstance(value, str) or len(value) > 2000:
                raise ValueError("조사 필드는 2000자 이하 문자열이어야 합니다.")
        if entry["category"] not in research or entry["status"] not in {"documented", "measured", "unknown"}:
            raise ValueError("조사 분류 또는 확인 상태가 잘못됐습니다.")
        if not entry["topic"].strip() or not entry["finding"].strip():
            raise ValueError("조사 주제와 결과를 입력하세요.")
        try:
            checked = date.fromisoformat(entry["checked_on"])
        except ValueError as error:
            raise ValueError("확인일은 YYYY-MM-DD 형식이어야 합니다.") from error
        if checked.isoformat() != entry["checked_on"]:
            raise ValueError("확인일은 YYYY-MM-DD 형식이어야 합니다.")
        if entry["status"] != "unknown" and not entry["source"].strip():
            raise ValueError("확인한 자료에는 출처 또는 측정 기록 경로가 필요합니다.")
        if entry["status"] == "documented":
            url = urlsplit(entry["source"])
            if url.scheme not in {"https", "http"} or not url.hostname:
                raise ValueError("문서 근거에는 HTTP(S) 출처 URL이 필요합니다.")
        research[entry["category"]].append(copy.deepcopy(entry))
    result = copy.deepcopy(brief)
    result["research"] = research
    result["feasibility"] = "not_assessed"
    result["next"] = "조사 근거와 미확인 항목을 검토하고 축소 선택지를 준비하세요."
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="기획에 조사 자료를 연결 (자동 조사·승인 없음)")
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        result = attach(brief, evidence)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print("SAVED: 조사 기록 저장. 구현 가능성·명세 승인은 미확정.")
        return 0
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
