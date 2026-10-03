import unittest

from planned_probe import bounded_step


class PlannedProbeTests(unittest.TestCase):
    def test_forward(self):
        self.assertEqual(bounded_step(3, 2, 10), 5)

    def test_backward(self):
        self.assertEqual(bounded_step(7, -2, 10), 5)

    def test_lower_bound(self):
        self.assertEqual(bounded_step(2, -8, 10), 0)

    def test_upper_bound(self):
        self.assertEqual(bounded_step(8, 9, 10), 10)

    def test_no_step(self):
        self.assertEqual(bounded_step(4, 0, 10), 4)

    def test_zero_maximum(self):
        self.assertEqual(bounded_step(0, 3, 0), 0)


if __name__ == "__main__":
    unittest.main()