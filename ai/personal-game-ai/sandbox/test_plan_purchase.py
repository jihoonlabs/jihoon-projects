import unittest

from plan_purchase import purchase


class PurchaseTests(unittest.TestCase):
    def test_affordable(self):
        self.assertEqual(purchase(10, 4), (6, True))

    def test_exact_money(self):
        self.assertEqual(purchase(4, 4), (0, True))

    def test_insufficient(self):
        self.assertEqual(purchase(3, 4), (3, False))

    def test_free(self):
        self.assertEqual(purchase(3, 0), (3, True))


if __name__ == "__main__":
    unittest.main()