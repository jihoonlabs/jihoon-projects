import argparse
import json
from datetime import datetime
from pathlib import Path

from ask_ai import ask_model
from create_loop import prepare_create
from edit_loop import prepare_edit
from read_context import read_context

BASE_DIR = Path(__file__).resolve().parent
MAX_TASKS = 8
MAX_ATTEMPTS = 3


def validate_options(goal, allowed):
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("승인된 목표가 필요합니다.")
    if len(goal) > 4000:
        raise ValueError("목표는 4000자 이내여야 합니다.")
    if not isinstance(allowed, list) or not 1 <= len(allowed) <= MAX_TASKS:
        raise ValueError("허용 작업은 1~8개여야 합니다.")

    seen = set()
    snapshots = []
    for item in allowed:
        if not isinstance(item, dict) or set(item) != {
            "kind", "target", "test_module"
        }:
            raise ValueError("허용 작업은 kind·target·test_module만 갖습니다.")
        if item["kind"] not in ("edit", "create"):
            raise ValueError("kind는 edit 또는 create여야 합니다.")
        prepare = prepare_create if item["kind"] == "create" else prepare_edit
        target, test = prepare(
            item["target"], goal, item["test_module"]
        )
        canonical = target.resolve()
        if canonical in seen:
            raise ValueError("같은 대상을 중복 지정할 수 없습니다.")
        seen.add(canonical)
        snapshots.append((
            target,
            test,
            target.read_bytes() if item["kind"] == "edit" else None,
            test.read_bytes(),
        ))
    return snapshots


def validate_plan(proposal, allowed, goal):
    if not isinstance(proposal, dict) or set(proposal) != {"tasks"}:
        raise ValueError("tasks만 포함한 JSON 객체가 필요합니다.")
    items = proposal["tasks"]
    if not isinstance(items, list) or len(items) != len(allowed):
        raise ValueError("각 허용 대상에 작업 하나가 필요합니다.")

    contracts = {
        (item["kind"], item["target"], item["test_module"])
        for item in allowed
    }
    seen_ids = set()
    used = set()
    tasks = []

    for item in items:
        if not isinstance(item, dict) or set(item) != {
            "id", "kind", "target", "test_module", "prompt"
        }:
            raise ValueError("작업 필드가 잘못됐습니다.")
        task_id = item["id"]
        if (
            not isinstance(task_id, str)
            or not task_id.strip()
            or len(task_id) > 64
            or task_id in seen_ids
        ):
            raise ValueError("작업 id는 짧고 고유한 문자열이어야 합니다.")
        values = (item["kind"], item["target"], item["test_module"])
        if not all(isinstance(value, str) for value in values):
            raise ValueError("작업 계약은 문자열이어야 합니다.")
        if values not in contracts or values in used:
            raise ValueError("허용되지 않거나 중복된 작업입니다.")
        prompt = item["prompt"]
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("작업 요청이 비어 있습니다.")

        # 실행 요청에도 승인된 원래 목표를 보존한다.
        request = (
            "# 승인된 목표\n" + goal
            + "\n\n# 이번 작업\n" + prompt
        )
        prepare = prepare_create if item["kind"] == "create" else prepare_edit
        prepare(item["target"], request, item["test_module"])
        seen_ids.add(task_id)
        used.add(values)
        tasks.append({**item, "prompt": request, "status": "pending"})

    # 계획 작업이 다른 작업의 고정 테스트를 수정하지 못하게 한다.
    paths = []
    for task in tasks:
        prepare = prepare_create if task["kind"] == "create" else prepare_edit
        paths.append(prepare(
            task["target"], task["prompt"], task["test_module"]
        ))
    targets = {target.resolve() for target, _ in paths}
    if any(test.resolve() in targets for _, test in paths):
        raise ValueError("고정 테스트를 다른 작업 대상으로 사용할 수 없습니다.")
    return tasks


def generate_plan(goal, allowed, model=None):
    context = read_context()
    snapshots = validate_options(goal, allowed)
    allowed = [dict(item) for item in allowed]
    model = ask_model if model is None else model

    def check_unchanged():
        if read_context() != context:
            raise RuntimeError("작업 문맥이 변경됐습니다.")
        validate_options(goal, allowed)
        for target, test, original, fixed in snapshots:
            if test.read_bytes() != fixed:
                raise RuntimeError("고정 테스트가 외부에서 변경됐습니다.")
            if original is not None and target.read_bytes() != original:
                raise RuntimeError("대상이 외부에서 변경됐습니다.")

    output = BASE_DIR / "outputs"
    output.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    folder = output / f"plan_{stamp}"
    folder.mkdir()
    (folder / "request.json").write_text(
        json.dumps(
            {"goal": goal, "allowed": allowed},
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    feedback = "아직 계획을 검사하지 않았습니다."
    for attempt in range(1, MAX_ATTEMPTS + 1):
        check_unchanged()
        prompt = (
            context
            + "\n\n# 승인된 목표\n" + goal
            + "\n\n# 허용 작업\n"
            + json.dumps(allowed, ensure_ascii=False)
            + "\n\n허용 대상마다 작업 하나를 만들고 실행 순서로 배열하세요. "
            "대상·kind·test_module은 그대로 사용하세요. "
            "목표 밖의 기능이나 명령을 추가하지 마세요. "
            "각 요청에 필요한 구현 조건을 구체적으로 적으세요. "
            "파일 수정·실행·검사를 했다고 주장하지 마세요. "
            "Markdown 없이 다음 형태의 JSON 객체만 반환하세요:\n"
            '{"tasks":[{"id":"001","kind":"edit",'
            '"target":"sandbox/example.py",'
            '"test_module":"test_example","prompt":"구현 요청"}]}\n'
            "# 이전 계획 검사 결과\n" + feedback
        )
        print(f"AI 계획 시도 {attempt}/{MAX_ATTEMPTS}", flush=True)
        answer = model(prompt)
        check_unchanged()
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("AI 응답이 비어 있습니다.")
        (folder / f"answer_{attempt}.txt").write_text(
            answer, encoding="utf-8"
        )
        try:
            tasks = validate_plan(json.loads(answer), allowed, goal)
        except ValueError as error:
            feedback = str(error)
            print("계획 검사 실패:", feedback)
            continue
        check_unchanged()
        path = folder / "tasks.json"
        with path.open("x", encoding="utf-8") as stream:
            stream.write(
                json.dumps(tasks, ensure_ascii=False, indent=2) + "\n"
            )
        return path

    raise RuntimeError(f"계획 생성 실패. 기록: {folder}")


def main():
    parser = argparse.ArgumentParser(description="승인된 목표의 작업 계획 생성")
    parser.add_argument("--request", required=True, type=Path)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    if not isinstance(request, dict) or set(request) != {"goal", "allowed"}:
        raise ValueError("입력은 goal·allowed를 갖는 JSON 객체여야 합니다.")
    path = generate_plan(request["goal"], request["allowed"])
    print("계획 저장:", path)


if __name__ == "__main__":
    main()