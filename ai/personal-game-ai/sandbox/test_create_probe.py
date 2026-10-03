import unittest

from generated_probe import bounded_step


class CreateProbeTests(unittest.TestCase):
    def test_forward(self):
        self.assertEqual(bounded_step(10, 3, 20), 13)

    def test_backward(self):
        self.assertEqual(bounded_step(10, -3, 20), 7)

    def test_lower_bound(self):
        self.assertEqual(bounded_step(2, -10, 20), 0)

    def test_upper_bound(self):
        self.assertEqual(bounded_step(18, 10, 20), 20)

    def test_no_step(self):
        self.assertEqual(bounded_step(8, 0, 20), 8)

    def test_zero_maximum(self):
        self.assertEqual(bounded_step(0, 10, 0), 0)


if __name__ == "__main__":
    unittest.main()
