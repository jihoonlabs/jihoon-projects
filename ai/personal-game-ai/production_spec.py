"""Build a reviewable specification; bind explicit approval to its content."""

import argparse
import copy
import hashlib
import json
from pathlib import Path

from downscale_choice import prepare_choices


def digest(spec):
    return hashlib.sha256(json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def build(brief, details):
    if not isinstance(brief, dict) or brief.get("stage") != "needs_specification":
        raise ValueError("사용자가 축소안을 선택한 기획이 필요합니다.")
    choices = brief.get("choices")
    if not isinstance(choices, dict) or choices.get("selected") is None:
        raise ValueError("축소안 선택이 없습니다.")
    source = copy.deepcopy(brief)
    source["stage"] = "needs_research"
    checked = prepare_choices(source, {"device": source.get("device", {}).get("id"), "options": choices.get("options")}, choices["selected"])
    fields = {"scope", "rules", "controls", "display_defaults", "resource_budget", "acceptance", "unverified"}
    if not isinstance(details, dict) or set(details) != fields:
        raise ValueError("명세 상세 필드가 잘못됐습니다.")
    for key, values in details.items():
        if not isinstance(values, list) or not 1 <= len(values) <= 20 or any(not isinstance(v, str) or not v.strip() or len(v) > 1000 for v in values):
            raise ValueError(key + "는 1~1000자 항목 1~20개여야 합니다.")
    spec = {"schema_version": 1, "brief": checked, "details": copy.deepcopy(details)}
    return {"stage": "review_specification", "specification": spec, "digest": digest(spec), "approval": None}


def approve(record, expected_digest):
    if not isinstance(record, dict) or record.get("stage") != "review_specification" or record.get("approval") is not None:
        raise ValueError("미승인 검토 명세가 필요합니다.")
    spec = record.get("specification")
    if not isinstance(spec, dict) or set(spec) != {"schema_version", "brief", "details"} or spec["schema_version"] != 1:
        raise ValueError("명세 형식이 잘못됐습니다.")
    rebuilt = build(spec["brief"], spec["details"])
    actual = rebuilt["digest"]
    if not isinstance(expected_digest, str) or record.get("digest") != actual or expected_digest != actual:
        raise ValueError("명세가 변경됐거나 검토 digest가 다릅니다. 다시 검토하세요.")
    result = copy.deepcopy(record)
    result["stage"] = "specification_approved"
    result["approval"] = {"digest": actual, "method": "explicit_digest"}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="제작 명세 작성·명시 승인 기록 (게임 생성 없음)")
    parser.add_argument("--brief", type=Path)
    parser.add_argument("--details", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--approve")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.record is not None or args.approve is not None:
            if args.record is None or args.approve is None or args.brief is not None or args.details is not None:
                raise ValueError("승인은 --record와 --approve만 함께 사용하세요.")
            result = approve(json.loads(args.record.read_text(encoding="utf-8")), args.approve)
        else:
            if args.brief is None or args.details is None:
                raise ValueError("명세 작성에는 --brief와 --details가 필요합니다.")
            result = build(json.loads(args.brief.read_text(encoding="utf-8")), json.loads(args.details.read_text(encoding="utf-8")))
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(result["stage"] + ": " + result["digest"])
        return 0
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
