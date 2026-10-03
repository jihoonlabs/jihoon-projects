import unittest

from movement import move_player


class MovementTests(unittest.TestCase):
    def test_horizontal_movement(self):
        self.assertEqual(move_player(10, 10, 1, 0, 60, 28), (11, 10))
        self.assertEqual(move_player(10, 10, -1, 0, 60, 28), (9, 10))

    def test_vertical_movement(self):
        self.assertEqual(move_player(10, 10, 0, 1, 60, 28), (10, 11))
        self.assertEqual(move_player(10, 10, 0, -1, 60, 28), (10, 9))

    def test_no_input_keeps_position(self):
        self.assertEqual(move_player(10, 10, 0, 0, 60, 28), (10, 10))

    def test_diagonal_movement(self):
        self.assertEqual(move_player(10, 10, 1, -1, 60, 28), (11, 9))

    def test_lower_bounds(self):
        self.assertEqual(move_player(0, 0, -1, -1, 60, 28), (0, 0))

    def test_upper_bounds(self):
        self.assertEqual(move_player(60, 28, 1, 1, 60, 28), (60, 28))

    def test_large_steps_are_clamped(self):
        self.assertEqual(move_player(10, 10, 100, -100, 60, 28), (60, 0))

    def test_bounds_are_not_hardcoded(self):
        self.assertEqual(move_player(3, 2, 5, 5, 4, 3), (4, 3))
        self.assertEqual(move_player(0, 0, 1, 1, 0, 0), (0, 0))


if __name__ == "__main__":
    unittest.main()