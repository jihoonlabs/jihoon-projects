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
                self.assertEqual(left,{(2*x+6-px,py) for px,py in right},
                                 (pose,frame))

    def test_punch_arm_is_straight_and_extends_in_two_frames(self):
        x,y=24,28
        for rightward in (True,False):
            first=self.pixels(game.attack_limb_runs('punch',0,rightward,x,y))
            extended=self.pixels(game.attack_limb_runs('punch',2,rightward,x,y))
            self.assertNotEqual(first,extended)
            for pixels in (first,extended):
                rows={py:{px for px,yy in pixels if yy==py} for py in (y+2,y+3)}
                self.assertEqual(rows[y+2],rows[y+3])
                self.assertEqual(max(rows[y+2])-min(rows[y+2])+1,len(rows[y+2]))
                self.assertEqual(self.component_count_pixels(pixels),1)
            if rightward:
                self.assertGreater(max(px for px,py in extended),x+7)
            else:
                self.assertLess(min(px for px,py in extended),x-1)

    def test_kick_has_one_planted_foot_and_one_raised_leg(self):
        x,y=24,28
        state={'player_attack_cooldown':8,'attack_kind':'kick'}
        self.assertEqual(game.character_body(state,True)[4:],(0,0))
        for rightward in (True,False):
            chamber=self.pixels(game.attack_limb_runs('kick',0,rightward,x,y))
            extended=self.pixels(game.attack_limb_runs('kick',2,rightward,x,y))
            self.assertNotEqual(chamber,extended)
            for pixels in (chamber,extended):
                # Only the supporting shoe reaches the floor row.
                self.assertEqual(sum(py==y+6 for px,py in pixels),2)
                self.assertEqual(self.component_count_pixels(pixels),2)
            self.assertTrue(any(py<y+6 for px,py in extended))

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
