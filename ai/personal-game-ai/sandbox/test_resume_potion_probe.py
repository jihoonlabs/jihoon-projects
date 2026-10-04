import unittest
from unittest.mock import patch
from resume_potion_probe import use_potion
import resume_potion_probe
import resume_health_probe

class TestResumePotionProbe(unittest.TestCase):
    def test_case_1(self):
        result = use_potion(5, 10, 2)
        self.assertEqual(result, (9, 1))

    def test_case_2(self):
        result = use_potion(10, 10, 2)
        self.assertEqual(result, (10, 2))

    def test_case_3(self):
        result = use_potion(5, 10, 0)
        self.assertEqual(result, (5, 0))

    def test_case_4(self):
        self.assertIs(resume_potion_probe.heal, resume_health_probe.heal)
        with patch('resume_potion_probe.heal', return_value=7) as mocked:
            result = use_potion(5, 10, 2)
            mocked.assert_called_once_with(5, 4, 10)
            self.assertEqual(result, (7, 1))
