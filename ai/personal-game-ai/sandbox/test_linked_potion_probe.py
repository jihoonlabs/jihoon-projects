import unittest
from unittest.mock import patch
import linked_health_probe
import linked_potion_probe
from linked_potion_probe import use_potion

class TestLinkedPotionProbe(unittest.TestCase):
    def test_case_1(self):
        self.assertEqual(use_potion(100, 100, 3), (100, 3))

    def test_case_2(self):
        self.assertEqual(use_potion(50, 100, 2), (54, 1))

    def test_case_3(self):
        self.assertEqual(use_potion(50, 100, 0), (50, 0))

    def test_case_4(self):
        self.assertIs(
            linked_potion_probe.heal,
            linked_health_probe.heal,
        )
        with patch("linked_potion_probe.heal", return_value=77) as mocked:
            result = use_potion(50, 100, 2)
            mocked.assert_called_once_with(50, 4, 100)
            self.assertEqual(result, (77, 1))
