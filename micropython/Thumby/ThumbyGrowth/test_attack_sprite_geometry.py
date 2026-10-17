"""Attack limb rectangles overlap the old, smaller fighter silhouette."""
import unittest
import test_ThumbyGrowth  # installs the Thumby API test double
import ThumbyGrowth as game


class AttackSpriteGeometryTests(unittest.TestCase):
    def test_punch_reach_animates_and_stays_connected_in_both_directions(self):
        for rightward in (True, False):
            first=game.attack_limb_rects('punch',0,rightward,24,28)
            extended=game.attack_limb_rects('punch',2,rightward,24,28)
            self.assertNotEqual(first,extended)
            for shapes in (first,extended):
                self.assertEqual(self.component_count(shapes),1)

    def test_kick_chambers_and_extends_from_the_hip(self):
        for rightward in (True, False):
            chamber=game.attack_limb_rects('kick',0,rightward,24,28)
            extended=game.attack_limb_rects('kick',2,rightward,24,28)
            self.assertNotEqual(chamber,extended)
            self.assertEqual(self.component_count(chamber),1)
            self.assertEqual(self.component_count(extended),1)

    @staticmethod
    def component_count(shapes):
        pixels=set()
        for x,y,width,height,color in shapes:
            if color:
                pixels.update((px,py) for px in range(x,x+width)
                              for py in range(y,y+height))
        count=0
        while pixels:
            count+=1
            stack=[pixels.pop()]
            while stack:
                x,y=stack.pop()
                for neighbor in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if neighbor in pixels:
                        pixels.remove(neighbor)
                        stack.append(neighbor)
        return count


if __name__ == '__main__':
    unittest.main()
