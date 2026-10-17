"""Check attack limbs remain readable after the shared fighter is scaled."""
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
                self.assertEqual(left,{(2*x+5-px,py) for px,py in right},
                                 (pose,frame))
                self.assertEqual(max(px for px,py in right)-(x+2.5),
                                 (x+2.5)-min(px for px,py in left),
                                 (pose,frame))

    def test_punch_arm_is_straight_and_extends_in_two_frames(self):
        x,y=24,28
        for rightward in (True,False):
            first=self.pixels(game.attack_limb_runs('punch',0,rightward,x,y))
            extended=self.pixels(game.attack_limb_runs('punch',2,rightward,x,y))
            self.assertNotEqual(first,extended)
            for pixels in (first,extended):
                upper={px for px,py in pixels if py==y+2}
                lower={px for px,py in pixels if py==y+3}
                self.assertEqual(upper,lower)
                self.assertEqual(max(upper)-min(upper)+1,len(upper))
                self.assertEqual(self.component_count_pixels(pixels),1)
            if rightward:
                self.assertLessEqual(max(px for px,py in extended),x+8)
                self.assertEqual(max(px for px,py in extended),x+8)
            else:
                self.assertGreaterEqual(min(px for px,py in extended),x-3)
                self.assertEqual(min(px for px,py in extended),x-3)

    def test_kick_has_a_broad_planted_shoe_and_straight_two_pixel_bar(self):
        x,y=24,28
        state={'player_attack_cooldown':8,'attack_kind':'kick'}
        self.assertEqual(game.character_body(state,True)[4:],(0,0))
        for rightward in (True,False):
            chamber=self.pixels(game.attack_limb_runs('kick',0,rightward,x,y))
            extended=self.pixels(game.attack_limb_runs('kick',2,rightward,x,y))
            self.assertNotEqual(chamber,extended)
            shoe_x=x-2 if rightward else x+3
            for pixels,reach in ((chamber,2),(extended,4)):
                # The shoe has a rounded 3/5-pixel profile and no thin leg
                # connecting it to the body.
                self.assertEqual({px for px,py in pixels if py==y+5},
                                 set(range(shoe_x+1,shoe_x+4)))
                self.assertEqual({px for px,py in pixels if py==y+6},
                                 set(range(shoe_x,shoe_x+5)))
                self.assertFalse(any(py==y+2 for px,py in pixels))
                self.assertEqual(self.component_count_pixels(pixels),2)
                for py in (y+3,y+4):
                    bar={px for px,yy in pixels if yy==py and
                         (px>=x+4 if rightward else px<=x+1)}
                    if rightward:
                        self.assertEqual(bar,set(range(x+4,x+5+reach)))
                    else:
                        self.assertEqual(bar,set(range(x-reach+1,x+2)))
            self.assertEqual({px for px,py in extended if py==y+3},
                             {px for px,py in extended if py==y+4})
            if rightward:
                self.assertEqual(max(px for px,py in extended),x+8)
            else:
                self.assertEqual(min(px for px,py in extended),x-3)

    @staticmethod
    def pixels(shapes):
        return {(x+dx,y+dy) for x,y,width,height,color in shapes if color
                for dx in range(width) for dy in range(height)}

    @staticmethod
    def component_count_pixels(pixels):
        remaining=set(pixels)
        count=0
        while remaining:
            count+=1
            stack=[remaining.pop()]
            while stack:
                x,y=stack.pop()
                for neighbor in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        stack.append(neighbor)
        return count


if __name__ == '__main__':
    unittest.main()
