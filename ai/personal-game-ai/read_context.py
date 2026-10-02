import json
import subprocess
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().with_name("target.json")


def git_output(root, *arguments):
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()


def read_context(config_path=CONFIG_PATH):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))

    if not isinstance(config, dict):
        raise ValueError("설정은 JSON 객체여야 합니다.")

    for key in ("repository_root", "expected_branch", "branch_document"):
        if not isinstance(config.get(key), str) or not config[key].strip():
            raise ValueError(f"유효한 문자열이 필요합니다: {key}")

    code_files = config.get("code_files")
    if not isinstance(code_files, list) or not all(
        isinstance(path, str) and path.strip() for path in code_files
    ):
        raise ValueError("code_files는 경로 문자열 목록이어야 합니다.")

    limit = config.get("max_context_chars")
    if type(limit) is not int or limit <= 0:
        raise ValueError("max_context_chars는 양의 정수여야 합니다.")

    root = (config_path.parent / config["repository_root"]).resolve()
    actual_root = Path(git_output(root, "rev-parse", "--show-toplevel")).resolve()
    if root != actual_root:
        raise ValueError("repository_root는 저장소 최상단이어야 합니다.")

    branch = git_output(root, "branch", "--show-current")
    if branch != config["expected_branch"]:
        raise RuntimeError(
            f"브랜치 불일치: 예상 {config['expected_branch']}, 실제 {branch}"
        )

    document = Path(config["branch_document"])
    if document.suffix.lower() != ".md" or document.parts[:1] != ("docs",):
        raise ValueError("브랜치 문서는 docs/ 아래의 MD여야 합니다.")

    files = ["AGENTS.md", config["branch_document"]] + code_files
    sections = []
    seen = set()
    total = 0

    for relative_path in files:
        relative = Path(relative_path)
        path = (root / relative).resolve()

        # 절대 경로·상위 경로·외부로 향하는 심볼릭 링크를 차단한다.
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"허용하지 않는 경로: {relative_path}")
        if root not in path.parents:
            raise ValueError(f"저장소 밖의 파일: {relative_path}")
        if path in seen:
            raise ValueError(f"중복 파일: {relative_path}")
        if relative_path in code_files and path.suffix.lower() == ".md":
            raise ValueError("추가 MD는 code_files에 넣을 수 없습니다.")
        seen.add(path)

        # 과도하게 큰 파일은 내용을 읽기 전에 차단한다.
        if path.stat().st_size > limit * 4:
            raise ValueError(f"파일 분량 초과: {relative_path}")

        content = path.read_text(encoding="utf-8")
        section = f"--- {relative_path} ---\n{content}"
        total += len(section) + (2 if sections else 0)
        if total > limit:
            raise ValueError(f"전체 문맥 분량 초과: {total} > {limit}")
        sections.append(section)

    return "\n\n".join(sections)


if __name__ == "__main__":
    context = read_context()
    print("설정·브랜치·경로 검사 통과")
    print("전체 문자 수:", len(context))