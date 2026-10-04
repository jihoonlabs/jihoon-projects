import unittest
from potion import use_potion

class TestPotion(unittest.TestCase):
    def test_case_1(self):
        self.assertEqual(use_potion(10, 10, 3), (10, 3))
    def test_case_2(self):
        self.assertEqual(use_potion(5, 10, 0), (5, 0))
    def test_case_3(self):
        self.assertEqual(use_potion(5, 10, 2), (9, 1))
    def test_case_4(self):
        self.assertEqual(use_potion(7, 10, 1), (10, 0))
