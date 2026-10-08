"""Record proposed reductions and an explicit choice, without approving a spec."""

import argparse
import copy
import json
from pathlib import Path

from research_record import attach


def prepare_choices(brief, proposal, selected=None):
    if not isinstance(brief, dict) or not isinstance(brief.get("research"), dict):
        raise ValueError("조사 기록이 연결된 기획이 필요합니다.")
    research = brief["research"]
    if set(research) != {"gameplay", "hardware"} or any(not isinstance(v, list) or not v for v in research.values()):
        raise ValueError("게임 형식과 기기 자료를 모두 기록하세요. 미확인은 unknown으로 남길 수 있습니다.")
    # Revalidate evidence and original-only policy at the boundary.
    checked = attach(brief, {"device": brief.get("device", {}).get("id"), "entries": research["gameplay"] + research["hardware"]})
    if not isinstance(proposal, dict) or set(proposal) != {"device", "options"} or proposal["device"] != checked["device"]["id"]:
        raise ValueError("축소안의 대상 기기가 기획과 다릅니다.")
    options = proposal["options"]
    if not isinstance(options, list) or not 2 <= len(options) <= 3:
        raise ValueError("비교할 축소안은 2~3개여야 합니다.")
    ids = set()
    for option in options:
        if not isinstance(option, dict) or set(option) != {"id", "title", "keep", "reduce", "unverified"}:
            raise ValueError("축소안 필드가 잘못됐습니다.")
        for key in ["id", "title"]:
            if not isinstance(option[key], str) or not option[key].strip() or len(option[key]) > 100:
                raise ValueError("축소안 ID와 제목은 1~100자여야 합니다.")
        if option["id"] in ids:
            raise ValueError("축소안 ID가 중복됐습니다.")
        ids.add(option["id"])
        for key in ["keep", "reduce", "unverified"]:
            value = option[key]
            if not isinstance(value, list) or not 1 <= len(value) <= 20 or any(not isinstance(v, str) or not v.strip() or len(v) > 1000 for v in value):
                raise ValueError("유지·축소·미검증 항목을 각각 1~20개 입력하세요.")
    if selected is not None and (not isinstance(selected, str) or selected not in ids):
        raise ValueError("존재하는 축소안 ID를 선택하세요.")
    result = copy.deepcopy(checked)
    result["choices"] = {"options": copy.deepcopy(options), "selected": selected}
    result["stage"] = "needs_specification" if selected is not None else "needs_choice"
    result["next"] = "선택안으로 명세를 작성해 승인을 받으세요." if selected is not None else "유지·축소·미검증 항목을 비교해 선택하세요."
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="축소안 비교와 사용자 선택 기록 (명세 승인 없음)")
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--select")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.interactive and args.select is not None:
            raise ValueError("--interactive와 --select 중 하나만 사용하세요.")
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
        proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
        result = prepare_choices(brief, proposal, args.select)
        if args.interactive:
            for option in result["choices"]["options"]:
                print(option["id"] + ": " + option["title"])
                for label, key in [("유지", "keep"), ("축소", "reduce"), ("미검증", "unverified")]:
                    print(label + ": " + "; ".join(option[key]))
            result = prepare_choices(brief, proposal, input("선택할 ID (명세 승인은 별도): ").strip())
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print("SAVED: " + result["stage"] + ". 명세 미승인.")
        return 0
    except (ValueError, OSError, EOFError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
