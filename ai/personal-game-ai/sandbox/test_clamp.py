import unittest

from clamp import clamp


class ClampTests(unittest.TestCase):
    def test_below_minimum(self):
        self.assertEqual(clamp(-5, 0, 10), 0)

    def test_above_maximum(self):
        self.assertEqual(clamp(15, 0, 10), 10)

    def test_inside_range(self):
        self.assertEqual(clamp(4, 0, 10), 4)

    def test_boundaries(self):
        self.assertEqual(clamp(0, 0, 10), 0)
        self.assertEqual(clamp(10, 0, 10), 10)

    def test_negative_range(self):
        self.assertEqual(clamp(-3, -10, -2), -3)

    def test_equal_boundaries(self):
        self.assertEqual(clamp(100, 7, 7), 7)

    def test_fractional_value(self):
        self.assertEqual(clamp(2.5, 0, 10), 2.5)


if __name__ == "__main__":
    unittest.main()