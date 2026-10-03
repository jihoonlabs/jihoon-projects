def order_tasks(tasks):
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 8:
        raise ValueError("계획 작업은 1~8개여야 합니다.")

    by_id = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("작업은 JSON 객체여야 합니다.")
        task_id = task.get("id")
        if (
            not isinstance(task_id, str)
            or not task_id.strip()
            or len(task_id) > 64
            or task_id in by_id
        ):
            raise ValueError("작업 id는 짧고 고유한 문자열이어야 합니다.")
        by_id[task_id] = task

    dependencies = {}
    for task_id, task in by_id.items():
        values = task.get("depends_on", [])
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value.strip() for value in values
        ):
            raise ValueError("depends_on은 작업 ID 문자열 목록이어야 합니다.")
        if len(values) != len(set(values)):
            raise ValueError("중복 의존성이 있습니다.")
        if task_id in values:
            raise ValueError("자기 자신에게 의존할 수 없습니다.")
        if any(value not in by_id for value in values):
            raise ValueError("계획에 없는 작업을 참조합니다.")
        dependencies[task_id] = values

    ordered = []
    visiting = set()
    completed = set()

    def visit(task_id):
        if task_id in visiting:
            raise ValueError("작업 의존성이 순환합니다.")
        if task_id in completed:
            return
        visiting.add(task_id)
        for dependency in dependencies[task_id]:
            visit(dependency)
        visiting.remove(task_id)
        completed.add(task_id)
        ordered.append(by_id[task_id])

    # 의존성 없는 기존 계획의 배열 순서는 유지한다.
    for task_id in by_id:
        visit(task_id)
    return ordered