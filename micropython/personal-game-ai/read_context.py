import subprocess
from pathlib import Path

GAME_ROOT = Path("/Users/parkjihoon/workspace/period-action-worktree")
EXPECTED_BRANCH = "feature/period-action-foundation"

FILES = (
    "AGENTS.md",
    "docs/period-action/FOUNDATION.md",
    "micropython/LanternRun/lantern_core.py",
)


def read_context():
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=GAME_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()

    # 다른 브랜치의 자료로 작업하지 않도록 먼저 확인한다.
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"브랜치 불일치: 예상 {EXPECTED_BRANCH}, 실제 {branch}"
        )

    sections = []
    for relative_path in FILES:
        content = (GAME_ROOT / relative_path).read_text(encoding="utf-8")
        sections.append(f"--- {relative_path} ---\n{content}")

    return "\n\n".join(sections)


if __name__ == "__main__":
    context = read_context()
    print("브랜치 확인 성공:", EXPECTED_BRANCH)
    for relative_path in FILES:
        print("읽은 파일:", relative_path)
    print("전체 문자 수:", len(context))