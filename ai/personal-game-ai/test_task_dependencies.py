import unittest

from task_dependencies import order_tasks


class DependencyTests(unittest.TestCase):
    def task(self, task_id, dependencies=None):
        task = {"id": task_id}
        if dependencies is not None:
            task["depends_on"] = dependencies
        return task

    def test_independent_order_is_preserved(self):
        tasks = [self.task("b"), self.task("a")]
        self.assertEqual(order_tasks(tasks), tasks)

    def test_dependency_is_ordered_first(self):
        tasks = [self.task("b", ["a"]), self.task("a")]
        self.assertEqual(
            [task["id"] for task in order_tasks(tasks)], ["a", "b"]
        )

    def test_shared_dependency_runs_once(self):
        tasks = [
            self.task("c", ["a", "b"]),
            self.task("b", ["a"]),
            self.task("a"),
        ]
        self.assertEqual(
            [task["id"] for task in order_tasks(tasks)], ["a", "b", "c"]
        )

    def test_invalid_dependencies_are_rejected(self):
        cases = [
            [self.task("a", ["missing"])],
            [self.task("a", ["a"])],
            [self.task("a", ["b"]), self.task("b", ["a"])],
            [self.task("a", ["b", "b"]), self.task("b")],
            [self.task("a", "b"), self.task("b")],
            [self.task("a", [1])],
            [self.task("a"), self.task("a")],
            [],
        ]
        for tasks in cases:
            with self.subTest(tasks=tasks):
                with self.assertRaises(ValueError):
                    order_tasks(tasks)

    def test_ordering_does_not_modify_input(self):
        tasks = [self.task("b", ["a"]), self.task("a")]
        before = [{"id": "b", "depends_on": ["a"]}, {"id": "a"}]
        order_tasks(tasks)
        self.assertEqual(tasks, before)


if __name__ == "__main__":
    unittest.main()