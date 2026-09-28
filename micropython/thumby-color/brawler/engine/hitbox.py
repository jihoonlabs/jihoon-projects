class VolumeHitbox:
    def __init__(self, owner, range_x=16, depth_y=8, height_z=12, damage=10, knockback_x=3.0, hitstun_frames=8):
        self.owner = owner
        self.range_x = range_x
        self.depth_y = depth_y
        self.height_z = height_z
        self.damage = damage
        self.knockback_x = knockback_x
        self.hitstun_frames = hitstun_frames

    def check_overlap(self, target):
        # Owner and target self-check guard
        if self.owner == target:
            return False

        # Direction-based attack offset (Facing Right vs Left)
        direction = 1 if getattr(self.owner, 'facing_right', True) else -1
        attack_x = self.owner.x + (direction * self.range_x)

        # 3D Distance Overlap Check
        dx = abs(attack_x - target.x)
        dy = abs(self.owner.y - target.y)
        dz = abs(self.owner.z - target.z)

        return (dx <= self.range_x) and (dy <= self.depth_y) and (dz <= self.height_z)

    def resolve_impact(self, target):
        direction = 1 if getattr(self.owner, 'facing_right', True) else -1
        
        # Apply Hitstun and Velocity Impulse
        if hasattr(target, 'apply_hit'):
            target.apply_hit(
                damage=self.damage,
                knockback_x=direction * self.knockback_x,
                hitstun=self.hitstun_frames
            )