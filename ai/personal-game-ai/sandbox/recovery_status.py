"""Read-only recovery status formatting for the personal-game-ai workflow."""


def get_recovery_summary(
    workflow_step,
    task_status,
    recovery_available,
    decision_required=False,
    decision_question=None,
):
    """Return a status summary and ask only for an explicitly required decision.

    This function is intentionally pure: it reads only its arguments and does
    not inspect Git, files, processes, or the workflow directory.
    """
    if not isinstance(workflow_step, str) or not workflow_step.strip():
        raise ValueError("workflow_step must be a non-empty string")
    if not isinstance(task_status, str) or not task_status.strip():
        raise ValueError("task_status must be a non-empty string")
    if type(recovery_available) is not bool:
        raise ValueError("recovery_available must be a bool")
    if type(decision_required) is not bool:
        raise ValueError("decision_required must be a bool")

    questions = []
    if decision_required:
        if not isinstance(decision_question, str) or not decision_question.strip():
            raise ValueError("a Korean decision_question is required")
        question = decision_question.strip()
        letters = [character for character in question if character.isalpha()]
        hangul_letters = [
            character
            for character in letters
            if "\uac00" <= character <= "\ud7a3"
        ]
        if not hangul_letters or len(hangul_letters) * 2 < len(letters):
            raise ValueError("decision_question must be primarily in Korean")
        questions.append(question)

    recovery_text = "가능" if recovery_available else "불가"
    summary = (
        f"현재 작업 단계: {workflow_step}, 상태: {task_status}, "
        f"복구 가능: {recovery_text}"
    )
    return {
        "summary": summary,
        "workflow_step": workflow_step,
        "task_status": task_status,
        "recovery_available": recovery_available,
        "questions": questions,
    }
