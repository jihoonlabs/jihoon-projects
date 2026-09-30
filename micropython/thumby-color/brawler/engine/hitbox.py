class VolumeHitbox:
    def __init__(self, owner, range_x=16, depth_y=8, height_z=12, damage=10, knockback_x=3.0, hitstun_frames=8, shake_power=3.0):
        self.owner = owner
        self.range_x = range_x
        self.depth_y = depth_y
        self.height_z = height_z
        self.damage = damage
        self.knockback_x = knockback_x
        self.hitstun_frames = hitstun_frames
        self.shake_power = shake_power

    def set_spec(self, range_x=16, depth_y=8, height_z=12, damage=10, knockback_x=3.0, hitstun_frames=8, shake_power=3.0):
        self.range_x = range_x
        self.depth_y = depth_y
        self.height_z = height_z
        self.damage = damage
        self.knockback_x = knockback_x
        self.hitstun_frames = hitstun_frames
        self.shake_power = shake_power
        return self

    def check_overlap(self, target):
        if self.owner == target:
            return False

        direction = 1 if getattr(self.owner, 'facing_right', True) else -1
        # Calculate attack center X based on facing direction and range_x
        half_range = self.range_x * 0.5
        attack_center_x = self.owner.x + (direction * half_range)

        dx = abs(attack_center_x - target.x)
        dy = abs(self.owner.y - target.y)
        dz = abs(self.owner.z - target.z)

        return (dx <= half_range) and (dy <= self.depth_y) and (dz <= self.height_z)

    def resolve_impact(self, target, camera=None):
        direction = 1 if getattr(self.owner, 'facing_right', True) else -1

        if hasattr(target, 'apply_hit'):
            target.apply_hit(
                damage=self.damage,
                knockback_x=direction * self.knockback_x,
                hitstun=self.hitstun_frames
            )

        # Trigger Screen Shake
        if camera:
            camera.add_shake(self.shake_power)

        # Return Hitstop Frame Count (3 frames freeze on impact)
        return 3