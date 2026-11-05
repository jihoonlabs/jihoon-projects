import unittest
from stamina_recovery import calculate_stamina_recovery

class TestStaminaRecovery(unittest.TestCase):
    def test_case_1(self):
        self.assertEqual(calculate_stamina_recovery(50, 100, 10), 60)

    def test_case_2(self):
        self.assertEqual(calculate_stamina_recovery(95, 100, 10), 100)

    def test_case_3(self):
        with self.assertRaises(ValueError):
            calculate_stamina_recovery(-1, 100, 5)
