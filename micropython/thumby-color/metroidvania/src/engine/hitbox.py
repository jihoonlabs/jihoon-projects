class WeaponHitbox:
    def __init__(self, owner, rel_x, rel_y, width, height, duration_frames):
        self.owner = owner
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.w = width
        self.h = height
        self.duration = duration_frames
        self.active = True

    def get_bbox(self):
        if self.owner.facing_right:
            abs_x = self.owner.x + self.owner.width + self.rel_x
        else:
            abs_x = self.owner.x - self.w - self.rel_x
            
        abs_y = self.owner.y + self.rel_y
        return AABB(abs_x, abs_y, self.w, self.h)

    def update(self):
        if self.duration > 0:
            self.duration -= 1
        else:
            self.active = False