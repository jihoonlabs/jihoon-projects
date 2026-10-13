
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess
import ask_ai
import create_loop
import edit_loop
import implementation_link

BASE = Path(__file__).resolve().parents[3] / "ai" / "personal-game-ai"

def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(value)

def main():
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], text=True
    ).strip()
    if branch != "work/thumby-rpg-first-20261008":
        raise SystemExit("작업 브랜치가 달라 중단합니다.")
    if ask_ai.payload.get("model") != "qwen3-coder:30b":
        raise SystemExit("요청 모델이 달라 중단합니다.")
    options = ask_ai.model_options()
    if options["num_ctx"] != 32768 or options["num_predict"] != 16384:
        raise SystemExit("문맥32768/출력16384 설정이 필요합니다.")

    manifest = BASE / "outputs/test_plan_20261012_083518_807142/tests.json"
    tests_sha = "23ea8a184a374aa7f1cc62300e0025124c828ea66b79b0af7061d1825a11c8d6"
    envelope, tests, _ = implementation_link.read_confirmed(manifest, tests_sha)
    design = BASE / "outputs/design_20261011_232344_146552/design.json"
    protected = {
        p: p.read_bytes() for p in (
            manifest, manifest.with_name("confirmation.json"),
            design, design.with_name("approval.json"),
        )
    }
    context = edit_loop.read_context()
    directory, _ = edit_loop.game_location()
    expected_directory = BASE.parent.parent / "micropython/ThumbyGrowth"
    if directory.resolve() != expected_directory.resolve():
        raise SystemExit("게임 대상 경로가 달라 중단합니다.")

    fixed = next(f for f in tests["files"] if f["id"] == "001")
    test_path = directory / fixed["filename"]
    test_bytes = fixed["code"].encode("utf-8")
    if test_path.read_bytes() != test_bytes:
        raise SystemExit("고정 테스트가 달라 중단합니다.")

    source = BASE / "outputs/create_20261012_093037_102467/candidate_1.py"
    if source.is_symlink() or not source.is_file():
        raise SystemExit("검증한 저장 코드를 찾지 못했습니다.")
    working_code = source.read_text(encoding="utf-8")
    compile(working_code, str(source), "exec")
    functions = next(f for f in envelope["design"]["files"] if f["id"] == "001")
    shared = next(
        f for item in envelope["design"]["files"] if item["id"] == "002"
        for f in item["functions"] if f["name"] == "step_frame"
    )
    selected = {"update_state", "is_valid_save_data"}
    before_folders = set((BASE / "outputs").glob("create_*"))
    calls = 0

    def check():
        for path, content in protected.items():
            if path.is_symlink() or path.read_bytes() != content:
                raise RuntimeError("승인 기록이 변경됐습니다.")
        if test_path.is_symlink() or test_path.read_bytes() != test_bytes:
            raise RuntimeError("고정 테스트가 변경됐습니다.")
        edit_loop.check_git_files(test_path, test_path)
        if edit_loop.read_context() != context:
            raise RuntimeError("작업 문맥이 변경됐습니다.")

    def model(engine_prompt):
        nonlocal working_code, calls
        check()
        calls += 1
        folders = [
            p for p in (BASE / "outputs").glob("create_*")
            if p not in before_folders and p.is_dir()
        ]
        if len(folders) != 1:
            raise RuntimeError("이번 기록 폴더를 구분하지 못했습니다.")
        folder = folders[0]
        tree = ast.parse(working_code)
        nodes = {
            n.name: n for n in tree.body
            if isinstance(n, ast.FunctionDef)
        }
        if not selected.issubset(nodes):
            raise RuntimeError("수정 대상 함수를 찾지 못했습니다.")

        feedback = engine_prompt.rsplit("\n이전 검사 결과:\n", 1)[-1]
        failed = re.findall(r"(?:FAIL|ERROR): ([^\n]+)", feedback)
        reasons = list(dict.fromkeys(
            line for line in feedback.splitlines()
            if line.startswith(("AssertionError:", "KeyError:", "TypeError:", "ValueError:"))
        ))
        prompt = (
            "기존 Thumby rules.py의 두 함수만 수정하세요.\n"
            "update_state와 is_valid_save_data의 전체 def 코드만 각각 반환하세요.\n"
            "다른 production 함수는 정의하지 마세요. 기존 다른 함수는 호출할 수 있습니다.\n"
            "최초 실패 원인: dict(state)는 owned를 복사하지 않습니다. "
            "new_state['owned']=list(state['owned'])가 필요하며 원본 owned를 변경하면 안 됩니다.\n"
            "저장 version/money/progress/장착ID는 정확한 int 검사로 bool을 거부하세요.\n"
            "이 두 오류를 고치면서 화면·메뉴·전투 계약 전체도 구현하세요.\n"
            "safe 확정은 A이며 R로 NEXT/SHOP/EQUIP/SAVE를 실행하지 않습니다.\n"
            "R새누름 판정은 이전 menu_r_held를 읽은 후 현재 값을 기록해야 합니다.\n"
            "공격·보상·장착·불변·스크롤·B우선·저장 요청을 승인 계약대로 처리하세요.\n"
            "반환 형식은 다음 JSON 하나입니다. 코드 블록과 설명은 붙이지 마세요:\n"
            '{"functions":{"update_state":"def update_state(state, inputs):\\n ...",'
            '"is_valid_save_data":"def is_valid_save_data(data):\\n ..."}}\n'
            "Python3.9와 MicroPython 호환. 주석·메시지는 한국어, 중국어 금지.\n"
            "\n승인 규칙 계약:\n"
            + json.dumps(functions, ensure_ascii=False)
            + "\n공유 화면 계약:\n" + json.dumps(shared, ensure_ascii=False)
            + "\n현재 두 함수:\n"
            + "\n\n".join(ast.get_source_segment(working_code, nodes[n]) for n in sorted(selected))
            + "\n고정 테스트 원문:\n" + fixed["code"]
            + "\n최근 실패 사례:\n" + "\n".join(failed)
            + "\n실패 원인:\n" + "\n".join(reasons)
        )
        save(folder / ("patch_prompt_%d.txt" % calls), prompt)
        print("두 함수 수정 요청:", calls, "요청 길이:", len(prompt), "자", flush=True)
        print("기록 폴더:", folder, flush=True)
        try:
            answer = ask_ai.ask_model(prompt)
        except ask_ai.ModelLengthError as error:
            save(
                folder / ("patch_length_%d.json" % calls),
                json.dumps(error.result, ensure_ascii=False, indent=2) + "\n",
            )
            raise
        save(folder / ("patch_raw_%d.txt" % calls), answer)
        body = answer.strip()
        lines = body.splitlines()
        if len(lines) >= 3 and lines[0].strip() in ("```json", "```") and lines[-1].strip() == "```":
            body = "\n".join(lines[1:-1])
        proposal = json.loads(body)
        if not isinstance(proposal, dict) or set(proposal) != {"functions"}:
            raise ValueError("수정 응답의 functions 형식이 잘못됐습니다.")
        replacements = proposal["functions"]
        if not isinstance(replacements, dict) or set(replacements) != selected:
            raise ValueError("승인한 두 함수만 수정할 수 있습니다.")

        lines = working_code.splitlines(keepends=True)
        patches = []
        for name, code in replacements.items():
            if not isinstance(code, str):
                raise ValueError("함수 코드는 문자열이어야 합니다.")
            parsed = ast.parse(code)
            if (
                len(parsed.body) != 1
                or not isinstance(parsed.body[0], ast.FunctionDef)
                or parsed.body[0].name != name
                or parsed.body[0].decorator_list
            ):
                raise ValueError("지정된 함수 def 하나만 반환해야 합니다.")
            old = nodes[name]
            patches.append((old.lineno - 1, old.end_lineno, code.rstrip() + "\n"))
        for start, end, code in sorted(patches, reverse=True):
            lines[start:end] = [code]
        merged = "".join(lines)
        compile(merged, "rules.py", "exec")
        check()
        working_code = merged
        save(folder / ("merged_%d.py" % calls), merged)
        return json.dumps({"action": "create", "code": merged}, ensure_ascii=False)

    print("모델: qwen3-coder:30b", flush=True)
    print("적용 옵션:", options, flush=True)
    result = create_loop.run_create(
        "game/rules.py",
        "승인 설계와 고정 테스트를 유지하며 저장된 rules.py의 두 함수를 Ollama로 수정합니다.",
        "test_rules",
        model=model,
    )
    print("\n결과:", json.dumps(result, ensure_ascii=False), flush=True)
    print("어댑터 생성·게임 커밋·push·실기 검증은 아직 하지 않았습니다.", flush=True)

if __name__ == "__main__":
    main()
