import unittest
from unittest.mock import patch

import dep_item


class ItemTests(unittest.TestCase):
    def test_use(self):
        self.assertEqual(dep_item.use_potion(3, 10, 2), (7, 1))

    def test_cap(self):
        self.assertEqual(dep_item.use_potion(8, 10, 1), (10, 0))

    def test_empty(self):
        self.assertEqual(dep_item.use_potion(3, 10, 0), (3, 0))

    def test_full_health_keeps_potion(self):
        self.assertEqual(dep_item.use_potion(10, 10, 2), (10, 2))

    def test_health_module_is_reused(self):
        with patch.object(dep_item, "heal", return_value=6) as heal:
            self.assertEqual(dep_item.use_potion(3, 10, 2), (6, 1))
        heal.assert_called_once_with(3, 4, 10)


if __name__ == "__main__":
    unittest.main()