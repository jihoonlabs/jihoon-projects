import unittest
from linked_health_probe import heal

class TestLinkedHealthProbe(unittest.TestCase):
    def test_case_1(self):
        self.assertEqual(heal(50, 20, 100), 70)

    def test_case_2(self):
        self.assertEqual(heal(80, 30, 100), 100)
