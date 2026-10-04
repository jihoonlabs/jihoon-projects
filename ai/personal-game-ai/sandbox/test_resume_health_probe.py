import unittest
from resume_health_probe import heal

class TestResumeHealthProbe(unittest.TestCase):
    def test_case_1(self):
        result = heal(5, 4, 10)
        self.assertEqual(result, 9)

    def test_case_2(self):
        result = heal(8, 4, 10)
        self.assertEqual(result, 10)
