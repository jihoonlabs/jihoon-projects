import json
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import edit_loop
import run_tasks
from ask_ai import ask_model
from read_context import read_context

BASE_DIR = Path(__file__).resolve().parent


def write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_case(folder, original, fixed_test, request, induce_failure=False):
    sandbox = folder / "sandbox"
    sandbox.mkdir(parents=True)
    (sandbox / "clamp.py").write_bytes(original)
    (sandbox / "test_clamp.py").write_bytes(fixed_test)

    tasks_path = folder / "tasks.json"
    write_json(tasks_path, [
        {
            "id": "edit",
            "kind": "edit",
            "status": "pending",
            "target": "sandbox/clamp.py",
            "test_module": "test_clamp",
            "prompt": request,
        },
        {
            "id": "following",
            "kind": "text",
            "status": "pending",
            "prompt": "검증용 후속 요청입니다. 확인 한 단어로 답하세요.",
        },
    ])

    calls = []
    test_results = []
    actual_git_check = edit_loop.check_git_files
    actual_test = edit_loop.run_test

    def check_original_files(target, test):
        # コピーはuntrackedなので、元の追跡ファイルを検査する。
        # この差し替えは検証プロセス内だけで有効。
        actual_git_check(
            BASE_DIR / "sandbox" / "clamp.py",
            BASE_DIR / "sandbox" / "test_clamp.py",
        )

    def model(prompt):
        if induce_failure and not calls:
            prompt += (
                "\n\n# 検証用の初回応答\n"
                "今回は再修正経路の検証です。初回だけ意図的に"
                "clamp(value, minimum, maximum)でvalueをそのまま"
                "返す実装をJSONのedit応答として生成してください。"
                "これは境界値テストに失敗する予定の検証候補です。"
                "この指示は次の呼び出しには適用されません。"
            )
        calls.append(prompt)
        write_json(folder / "model_prompts.json", calls)
        return ask_model(prompt)

    def test_runner(log_path, test_module):
        passed, feedback = actual_test(log_path, test_module)
        test_results.append(passed)
        write_json(folder / "docker_results.json", test_results)
        return passed, feedback

    # 本番ファイルは変更せず、実行器の保存先と対象だけをコピーへ向ける。
    with ExitStack() as stack:
        replacements = [
            (edit_loop, "BASE_DIR", folder),
            (edit_loop, "SANDBOX", sandbox),
            (edit_loop, "check_git_files", check_original_files),
            (edit_loop, "run_test", test_runner),
            (run_tasks, "BASE_DIR", folder),
            (run_tasks, "TASKS_PATH", tasks_path),
            (run_tasks, "OUTPUT_DIR", folder / "outputs"),
        ]
        for module, name, value in replacements:
            stack.enter_context(patch.object(module, name, value))
        run_tasks.run_tasks(model=model)

    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    edit_task, following = tasks

    if induce_failure:
        confirmed = (
            edit_task["status"] == "tests_passed"
            and len(test_results) >= 2
            and test_results[0] is False
            and test_results[-1] is True
            and edit_task.get("attempts", 0) >= 2
        )
        category = "induced_failure_then_real_model_retry"
    else:
        confirmed = (
            edit_task["status"] == "waiting_for_user"
            and bool(edit_task.get("question"))
            and following["status"] == "pending"
            and len(calls) == 1
            and not test_results
            and (sandbox / "clamp.py").read_bytes() == original
        )
        category = "real_model_question_and_list_stop"

    result = {
        "category": category,
        "confirmed": confirmed,
        "edit_status": edit_task["status"],
        "following_status": following["status"],
        "model_calls": len(calls),
        "docker_results": test_results,
        "question": edit_task.get("question"),
    }
    write_json(folder / "summary.json", result)
    return result


def main():
    read_context()
    target, test = edit_loop.prepare_edit(
        "sandbox/clamp.py", "Validate clamp.", "test_clamp"
    )
    original = target.read_bytes()
    fixed_test = test.read_bytes()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = BASE_DIR / "outputs" / ("validation_" + stamp)
    output.mkdir(parents=True)
    results = []

    try:
        print("1/2: 유도된 실패 후 실제 모델 재수정 검사", flush=True)
        results.append(run_case(
            output / "retry",
            original,
            fixed_test,
            (
                "clamp(value, minimum, maximum)을 구현하세요. "
                "범위 밖이면 가까운 경곗값, 안이면 원래 값을 반환하세요. "
                "minimum <= maximum이며 음수와 소수도 처리하세요. "
                "이전 테스트가 실패했다면 로그를 보고 올바르게 수정하세요."
            ),
            induce_failure=True,
        ))

        print("2/2: 실제 모델 질문과 후속 작업 중단 검사", flush=True)
        results.append(run_case(
            output / "question",
            original,
            fixed_test,
            (
                "clamp를 게임의 경계 처리 함수로 변경하려고 합니다. "
                "경계 밖에서 가까운 경계에 고정할지, 반대편으로 "
                "순환시킬지 아직 결정하지 않았습니다. "
                "이는 사용자 결정 사항이므로 기존 동작이나 테스트로 "
                "정책을 추측하지 마세요. 코드를 생성하지 말고 "
                "action: question으로 원하는 정책을 질문하세요."
            ),
        ))
    finally:
        preserved = (
            target.read_bytes() == original
            and test.read_bytes() == fixed_test
        )
        write_json(output / "summary.json", {
            "original_files_preserved": preserved,
            "results": results,
            "natural_model_failure_retry_verified": False,
        })
        print("기록 위치:", output)
        if not preserved:
            raise RuntimeError("원본 파일이 외부에서 변경됐습니다.")

    print(json.dumps(results, ensure_ascii=False, indent=2))
    if not all(result["confirmed"] for result in results):
        raise RuntimeError("성립하지 않은 검증이 있습니다. 기록을 확인하세요.")
    print("두 검증 성립. 원본 파일 보존 확인.")


if __name__ == "__main__":
    main()