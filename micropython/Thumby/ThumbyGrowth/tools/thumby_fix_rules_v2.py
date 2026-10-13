
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

BASE = Path(__file__).resolve().parents[4] / "ai" / "personal-game-ai"

def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(value)

def main():
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], text=True
    ).strip()
    if branch != json.loads((BASE / "target.json").read_text(encoding="utf-8"))["expected_branch"]:
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
    expected_directory = BASE.parent.parent / "micropython/Thumby/ThumbyGrowth"
    if directory.resolve() != expected_directory.resolve():
        raise SystemExit("게임 대상 경로가 달라 중단합니다.")

    fixed = next(f for f in tests["files"] if f["id"] == "001")
    test_path = directory / fixed["filename"]
    test_bytes = fixed["code"].encode("utf-8")
    if test_path.read_bytes() != test_bytes:
        raise SystemExit("고정 테스트가 달라 중단합니다.")

    source = BASE / "outputs/create_20261012_093322_377290/merged_3.py"
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
        prompt += "\n현재 코드를 그대로 반환하면 안 됩니다. 지난 세 응답은 같은 SHA였습니다.\nupdate_state의 분기 구조를 승인 계약대로 다시 구성하세요.\n이미 통과한 구매·장착·복사·재도전 동작도 유지하세요.\n\n1. 시작에서 state dict와 owned list를 각각 새로 복사합니다.\n   old_screen=state['screen_state']와 이전 menu_r_held를 먼저 읽습니다.\n   save_requested=False로 초기화하고 menu_r_held=inputs['R']를 매 호출 기록합니다.\n   R새누름은 이전False/현재True로 판정합니다.\n\n2. B를 다른 입력보다 먼저 처리하고 즉시 return합니다.\n   battle B -> pause, pause B -> battle.\n   shop/equip B -> safe.\n   상세 B -> 해당 목록이며 선택·스크롤은 보존합니다.\n   safe/defeat B는 동작하지 않습니다.\n   B 호출에서는 이동·공격·시간 진행·구매·장착을 처리하지 않습니다.\n   현재 코드의 마지막 elif B는 battle 분기 뒤라 도달할 수 없습니다. 제거하세요.\n\n3. 메뉴/상세/패배 상태는 처리 후 return합니다.\n   safe A NEXT는 HP=maxHP, x16/112, 방향R, combat_frame0,\n   양쪽대기0, 현재 진행도의 적스탯을 설정하고 battle로 전환합니다.\n   예: HP3/x55/frame9/대기7 상태도 결과는10/16/112/0/0입니다.\n   SHOP/EQUIP 진입도 선택·스크롤0입니다.\n   safe A SAVE는 선택3, pause A SAVE는 선택1이며\n   요청True를 반환해야 합니다. 함수 끝에서 다시False로 만들지 마세요.\n   요청 소비는 step_frame의 책임입니다.\n   pause RESUME은 전투 필드 보존 후 battle, 그 호출은 시간 정지입니다.\n\n4. shop/equip R새누름은 소유 여부와 무관하게 상세로 진입합니다.\n   이전 R 이력을 읽기 전에 현재 R로 덮어쓰지 마세요.\n   상세에서 A는 구매/장착·해제, U/D/L/R 동작은 없습니다.\n   목록↔상세 선택·스크롤은 보존하고 R held 재진입을 막습니다.\n   목록 U/D는 한쪽만 눌렸을 때 움직이며 safe/shop/equip 최대3,\n   pause 최대1입니다. 3행 스크롤을 맞추세요.\n\n5. battle 유지 호출만 frame+1, 대기감소, 이동, 적이동,\n   플레이어공격, 처치 또는 생존적공격, 패배 순서로 처리합니다.\n   이동은 실제 x가 바뀐 경우에만 direction을 바꿉니다.\n   x0에서 L 입력은 x0/direction R 유지입니다.\n   양쪽 캐릭터는8픽셀이며 겹치거나 통과하지 않습니다.\n   적은 증가한 짝수 frame에만 한 픽셀 접근하고 접촉에서 멈춥니다.\n\n6. 공격 거리는 중심점 차이가 아닙니다.\n   방향R 앞 간격=enemy_x-(player_x+8).\n   방향L 앞 간격=player_x-(enemy_x+8).\n   0..8만 명중합니다. 반대방향은 명중하지 않습니다.\n   x16/32는 간격8로 공격2/방어0이면 enemy_hp6->4입니다.\n   A입력/감소후대기0이면 빗나가도 플레이어대기15입니다.\n   대기2->1이면 공격불가, 대기1->0이면 공격가능합니다.\n\n7. 생존 적의 간격은 max(x둘)-(min(x둘)+8)입니다.\n   간격0..2/대기0에서만 공격하고 적대기30입니다.\n   x16/26에서 A면 플레이어HP10->8, 적HP6->4입니다.\n   플레이어 공격으로 죽은 적은 같은 호출에 반격하지 않습니다.\n\n8. 처치는 돈20/30, 진행도+1, HP=maxHP로 완전 회복합니다.\n   HP2 처치 후 HP3이 아니라10입니다.\n   비활성화·적HP/공격/방어0·safe 전환하고 추가보상하지 않습니다.\n   피해 후 HP는0이상으로 제한하고 HP0은defeat입니다.\n   재도전은 돈·소유·장착·진행도를 유지하고 장비스탯을 재계산합니다.\n\n9. is_valid_save_data의 장착ID도 정확한 int여야 합니다.\n   equipped_weapon이 None이 아니면\n   type(value) is int AND value in (0,1) AND owned[value]입니다.\n   equipped_armor도 같은 방식으로 (2,3)입니다.\n   True는1과 같아도 무기ID로 받아들이면 안 됩니다.\n   float ID도 거부하세요. 나머지 정확한6키·버전·돈·진행도·bool4개 검사 유지.\n\n전체 고정 테스트를 실제로 통과하도록 두 함수의 전체 def를 수정하세요.\n테스트를 변경하거나 구현하지 말고 JSON functions 형식만 반환하세요.\n"
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
        if ast.dump(ast.parse(merged)) == ast.dump(ast.parse(working_code)):
            save(folder / ("unchanged_%d.py" % calls), merged)
            raise RuntimeError("실질적으로 같은 코드가 반환되어 추가 실행을 중단합니다.")
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
