"""Attack limbs should stay attached in native 12x14 Thumby sprite art."""
import unittest
import test_ThumbyGrowth  # installs the Thumby API test double
import ThumbyGrowth as game


class AttackSpriteGeometryTests(unittest.TestCase):
    def lit_pixels(self, country, pose, frame=0):
        rows, cuts = game.period_sprite(country, pose, frame)
        return {(x, y) for y, row in enumerate(rows) for x in range(12)
                if row & (1 << (11-x))}

    def test_native_sprite_dimensions_are_compact(self):
        for country in range(3):
            for pose in ('idle', 'walk', 'punch', 'kick'):
                rows, details = game.period_sprite(country, pose)
                self.assertEqual((len(rows), len(details)), (14, 14))
                self.assertTrue(all(0 <= row < 1 << 12 for row in rows+details))

    def test_punch_fist_remains_joined_to_the_sleeve_through_extension(self):
        for country in range(3):
            for frame in range(3):
                pixels = self.lit_pixels(country, 'punch', frame)
                self.assertTrue(any(x >= 8 and 6 <= y <= 7 for x, y in pixels))
                self.assertEqual(self.component_count(pixels), 1)

    def test_kicking_shoe_grows_out_of_the_hip_not_beside_the_body(self):
        for country in range(3):
            bent = self.lit_pixels(country, 'kick', 0)
            extended = self.lit_pixels(country, 'kick', 1)
            self.assertEqual(self.component_count(bent), 1)
            self.assertEqual(self.component_count(extended), 1)
            self.assertIn((11, 13), extended)
            self.assertGreater(len(extended), len(bent))

    @staticmethod
    def component_count(pixels):
        remaining = set(pixels)
        count = 0
        while remaining:
            count += 1
            stack = [remaining.pop()]
            while stack:
                x, y = stack.pop()
                for neighbor in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        stack.append(neighbor)
        return count


if __name__ == '__main__':
    unittest.main()
