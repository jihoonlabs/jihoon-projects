"""Attack limb rectangles overlap the old, smaller fighter silhouette."""
import unittest
import test_ThumbyGrowth  # installs the Thumby API test double
import ThumbyGrowth as game


class AttackSpriteGeometryTests(unittest.TestCase):
    def test_attack_art_is_an_exact_mirror_with_matching_frame_timing(self):
        x,y=24,28
        for pose in ('punch','kick'):
            for frame in range(8):
                right=self.pixels(game.attack_limb_runs(pose,frame,True,x,y))
                left=self.pixels(game.attack_limb_runs(pose,frame,False,x,y))
                self.assertEqual(left,{(2*x+6-px,py) for px,py in right},
                                 (pose,frame))

    def test_punch_reach_animates_and_stays_connected_in_both_directions(self):
        x,y=24,28
        for rightward in (True, False):
            first=game.attack_limb_runs('punch',0,rightward,24,28)
            extended=game.attack_limb_runs('punch',2,rightward,24,28)
            self.assertNotEqual(first,extended)
            for shapes in (first,extended):
                self.assertEqual(self.component_count(shapes),1)
                width,height=self.bounds(shapes)
                self.assertEqual(height,2)
                self.assertLessEqual(width,5)
            extended_pixels=self.pixels(extended)
            if rightward:
                self.assertGreaterEqual(max(px for px,py in extended_pixels),x+8)
            else:
                self.assertLessEqual(min(px for px,py in extended_pixels),x-2)

    def test_kick_chambers_and_extends_from_the_hip(self):
        x,y=24,28
        for rightward in (True, False):
            chamber=game.attack_limb_runs('kick',0,rightward,24,28)
            extended=game.attack_limb_runs('kick',2,rightward,24,28)
            self.assertNotEqual(chamber,extended)
            self.assertEqual(self.component_count(chamber),1)
            self.assertEqual(self.component_count(extended),1)
            self.assertLessEqual(self.bounds(chamber)[0],3)
            width,height=self.bounds(extended)
            self.assertLessEqual(width,7)
            self.assertLessEqual(height,3)
            pixels=self.pixels(extended)
            if rightward:
                self.assertGreaterEqual(max(px for px,py in pixels),x+9)
            else:
                self.assertLessEqual(min(px for px,py in pixels),x-3)

    @staticmethod
    def bounds(shapes):
        pixels=[(x+dx,y+dy) for x,y,width,height,color in shapes if color
                for dx in range(width) for dy in range(height)]
        return (max(x for x,y in pixels)-min(x for x,y in pixels)+1,
                max(y for x,y in pixels)-min(y for x,y in pixels)+1)

    @staticmethod
    def pixels(shapes):
        return {(x+dx,y+dy) for x,y,width,height,color in shapes if color
                for dx in range(width) for dy in range(height)}

    @staticmethod
    def component_count(shapes):
        pixels=set()
        for x,y,width,height,color in shapes:
            if color:
                pixels.update((x+offset,y+row) for offset in range(width)
                              for row in range(height))
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
