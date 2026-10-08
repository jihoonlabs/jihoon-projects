"""Prepare a lossless engine request from an approved product specification."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

import production_spec
import read_context
import thumby_capabilities

SECTIONS = ("scope", "rules", "controls", "display_defaults", "resource_budget", "acceptance", "unverified")


def approved_spec(record):
    if not isinstance(record, dict) or set(record) != {"stage", "specification", "digest", "approval"}:
        raise ValueError("승인 명세 기록 형식이 잘못됐습니다.")
    if record["stage"] != "specification_approved" or record["approval"] != {
        "digest": record["digest"], "method": "explicit_digest"
    }:
        raise ValueError("명시적으로 승인된 제작 명세가 필요합니다.")
    review = copy.deepcopy(record)
    review.update(stage="review_specification", approval=None)
    # Reuse the original approval boundary instead of trusting a stored digest.
    production_spec.approve(review, record["digest"])
    return review["specification"]


def request_for(spec):
    brief = spec["brief"]
    selected = next(option for option in brief["choices"]["options"]
                    if option["id"] == brief["choices"]["selected"])
    goal = "승인 제작 명세를 구현하세요. 원본 표현·코드·데이터 복사 금지.\n" + json.dumps({
        "device": brief["device"], "settings": brief["settings"], "selected": selected,
    }, ensure_ascii=False, separators=(",", ":"))
    if len(goal) > 4000:
        raise ValueError("승인 목표가 생성기의 4000자 제한을 넘습니다. 내용을 자르지 않았습니다.")
    requirements = []
    for section in SECTIONS:
        text = "\n".join(spec["details"][section])
        prefix = section + ": "
        width = 500 - len(prefix)
        # Keep every character, including items longer than a single requirement.
        requirements.extend(prefix + text[start:start + width]
                            for start in range(0, len(text), width))
    if len(requirements) > 12 or len(set(requirements)) != len(requirements):
        raise ValueError("승인 명세가 고유 조건 12개 제한에 맞지 않습니다. 축약·누락 없이 중단했습니다.")
    return {"goal": goal, "requirements": requirements, "area": "game"}


def regular_file(path):
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)) or not path.is_file():
        raise ValueError("심볼릭 링크가 아닌 일반 파일을 지정하세요.")
    return path


def prepare(record, config_path, *, game_directory, expected_branch):
    spec = approved_spec(record)
    if spec["brief"]["device"]["id"] != "thumby":
        raise ValueError("현재 생성 요청 연결은 일반 Thumby만 지원합니다. Color 생성은 미지원입니다.")
    path = regular_file(config_path)
    data = path.read_bytes()
    config = json.loads(data)
    if not isinstance(config, dict):
        raise ValueError("대상 설정은 JSON 객체여야 합니다.")
    features = thumby_capabilities.selected(config)
    relative = Path(game_directory)
    if (relative.is_absolute() or len(relative.parts) != 2 or relative.parts[0] != "micropython"
            or not relative.name.isidentifier()):
        raise ValueError("게임 경로는 micropython/유효한게임이름이어야 합니다.")
    if (config.get("generation_profile") != "thumby"
            or config.get("edit_directory") != relative.as_posix()
            or config.get("expected_branch") != expected_branch):
        raise ValueError("선택한 기기·게임 경로·브랜치와 대상 설정이 다릅니다.")
    context = read_context.read_context(path)
    root = (path.parent / config["repository_root"]).resolve()
    target = root / relative
    if target.is_symlink() or target.resolve().parent != (root / "micropython").resolve():
        raise ValueError("게임 경로가 저장소 밖으로 향합니다.")
    if (root / "micropython").is_symlink() or not target.is_dir() or any(target.iterdir()):
        raise ValueError("새 게임을 위한 비어 있는 일반 폴더가 필요합니다. 기존 게임은 덮어쓰지 않습니다.")
    tracked = read_context.git_output(root, "ls-files", "--", relative.as_posix())
    if tracked:
        raise ValueError("삭제된 추적 파일도 있는 게임 폴더는 사용할 수 없습니다.")
    request = request_for(spec)
    if path.read_bytes() != data:
        raise RuntimeError("검사 중 대상 설정이 변경됐습니다.")
    return {
        "stage": "request_prepared", "specification_digest": record["digest"],
        "target_config_sha256": hashlib.sha256(data).hexdigest(),
        "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
        "binding": {"expected_branch": expected_branch, "edit_directory": relative.as_posix(),
                    "entry_filename": relative.name + ".py", "generation_profile": "thumby",
                    "thumby_features": sorted(features)},
        "request": request,
        "limitations": ["요청 변환은 API 지원·실기 성능·게임 완성 검증이 아닙니다.",
                        "추가 입력·저장 API는 target 설정의 thumby_features로 선택합니다. API 허용은 실기 동작 검증을 뜻하지 않습니다.",
                        "실행기는 자신의 target.json을 다시 검사합니다. 제품 승인은 설계·테스트 승인을 대신하지 않습니다."],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="승인 명세를 대상 설정과 대조하여 생성 요청 저장 (실행 없음)")
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--target-config", type=Path, required=True)
    parser.add_argument("--game-directory", required=True)
    parser.add_argument("--expected-branch", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        record = json.loads(regular_file(args.record).read_text(encoding="utf-8"))
        result = prepare(record, args.target_config, game_directory=args.game_directory,
                         expected_branch=args.expected_branch)
        output = args.output_dir.absolute()
        if any(item.is_symlink() for item in (output, *output.parents)):
            raise ValueError("출력 경로에 심볼릭 링크를 사용할 수 없습니다.")
        output.mkdir(exist_ok=False)
        for name, data in (("request.json", result["request"]), ("binding.json", result)):
            with (output / name).open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"stage": result["stage"], "request_file": str(output / "request.json"),
                          "limitations": result["limitations"]}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
