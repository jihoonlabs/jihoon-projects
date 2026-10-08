"""Delegate one step to an explicitly selected generation checkout."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def run(request, tool_dir, *, approve=None, confirm=None):
    if approve is not None and confirm is not None:
        raise ValueError("설계 승인과 테스트 확정은 한 번에 하나만 지정하세요.")
    request = Path(request).absolute()
    tool_dir = Path(tool_dir).absolute()
    script = tool_dir / "workflow.py"
    if request.is_symlink() or not request.is_file():
        raise ValueError("일반 요청 파일이 필요합니다.")
    if tool_dir.is_symlink() or not tool_dir.is_dir() or script.is_symlink() or not script.is_file():
        raise ValueError("workflow.py가 있는 일반 도구 폴더를 지정하세요.")
    command = [sys.executable, str(script), "--request", str(request)]
    if approve is not None:
        command += ["--approve-design", approve]
    if confirm is not None:
        command += ["--confirm-tests", confirm]
    # The selected engine owns branch/context checks, locks and approval digests.
    # Do not import it here or replace its target.json with the intake config.
    completed = subprocess.run(command, cwd=tool_dir, capture_output=True,
                               text=True, encoding="utf-8", check=False)
    try:
        result = json.loads(completed.stdout)
    except (ValueError, TypeError):
        result = {"stage": "blocked", "error": completed.stderr[-2000:] or "workflow JSON 응답이 없습니다."}
    if not isinstance(result, dict) or not isinstance(result.get("stage"), str):
        result = {"stage": "blocked", "error": "workflow 응답 형식이 잘못됐습니다."}
    if completed.returncode and "error" not in result:
        result["error"] = "workflow가 실패 코드로 종료됐습니다."
    result["request_file"] = str(request)
    return result


def main():
    parser = argparse.ArgumentParser(description="준비된 요청으로 기존 workflow 시작·검토 재개")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--tool-dir", type=Path, required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--approve-design")
    action.add_argument("--confirm-tests")
    args = parser.parse_args()
    try:
        result = run(args.request, args.tool_dir, approve=args.approve_design, confirm=args.confirm_tests)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if "error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
