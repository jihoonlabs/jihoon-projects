import unittest
from heal import heal

class TestHeal(unittest.TestCase):
    def test_case_1(self):
        self.assertEqual(heal(5, 3, 10), 8)
    def test_case_2(self):
        self.assertEqual(heal(8, 5, 10), 10)
