import unittest

from dep_health import heal


class HealthTests(unittest.TestCase):
    def test_heal(self):
        self.assertEqual(heal(3, 4, 10), 7)

    def test_cap(self):
        self.assertEqual(heal(8, 5, 10), 10)

    def test_zero(self):
        self.assertEqual(heal(3, 0, 10), 3)


if __name__ == "__main__":
    unittest.main()