import random
from entities.base import Entity
from engine.hitbox import VolumeHitbox

COLOR_ENEMY_IDLE = 0xF800
COLOR_ENEMY_CHASE = 0xFC00
COLOR_ENEMY_ATTACK = 0xF81F

class Enemy(Entity):
    def __init__(self, entity_id, x, y):
        super().__init__(entity_id, x, y, z=0.0, w=12, h=16, color=COLOR_ENEMY_IDLE)
        self.walk_speed = 1.0
        self.state = "PATROL"  # PATROL, CHASE, ATTACK, COOLDOWN
        self.patrol_timer = 0
        self.patrol_dir = 1
        self.attack_cooldown = 0
        self.attack_frame = 0

        # Sight & Attack Ranges
        self.sight_range_x = 96.0
        self.attack_range_x = 16.0
        self.attack_range_y = 6.0

        self.hitbox = VolumeHitbox(self, range_x=14, depth_y=6, height_z=12, damage=10, knockback_x=3.0, hitstun_frames=8)

    def update_ai(self, player, world_width=512):
        self.update_physics()

        # Lock AI during Hitstun
        if self.hitstun > 0:
            return

        # Cooldown reduction
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # Attack frame animation
        if self.attack_frame > 0:
            self.attack_frame -= 1
            if self.attack_frame == 0:
                self.state = "COOLDOWN"
                self.attack_cooldown = 30  # 1 sec cooldown
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist_x = abs(dx)
        dist_y = abs(dy)

        # Facing direction
        if dx != 0:
            self.facing_right = (dx > 0)

        # AI State Machine Behavior
        if self.state == "COOLDOWN":
            # Retreat slightly or stay back
            if self.attack_cooldown <= 0:
                self.state = "CHASE"
            else:
                self.color = COLOR_ENEMY_IDLE

        elif dist_x <= self.sight_range_x:
            self.state = "CHASE"
            self.color = COLOR_ENEMY_CHASE

            # 1. Y-Axis Alignment Phase (Priority 1)
            if dist_y > self.attack_range_y:
                self.y += (1.0 if dy > 0 else -1.0) * (self.walk_speed * 0.7)

            # 2. X-Axis Distance Closure Phase (Priority 2)
            if dist_x > self.attack_range_x:
                self.x += (1.0 if dx > 0 else -1.0) * self.walk_speed

            # 3. Attack Trigger
            if dist_x <= self.attack_range_x and dist_y <= self.attack_range_y and self.attack_cooldown <= 0:
                self.state = "ATTACK"
                self.attack_frame = 10
                self.color = COLOR_ENEMY_ATTACK

        else:
            # Idle Patrol
            self.state = "PATROL"
            self.color = COLOR_ENEMY_IDLE
            self.patrol_timer += 1
            if self.patrol_timer > 60:
                self.patrol_dir *= -1
                self.patrol_timer = 0
            self.x += self.patrol_dir * (self.walk_speed * 0.4)

        # Map Boundaries
        self.x = max(8.0, min(float(world_width - 16), self.x))
        self.y = max(58.0, min(112.0, self.y))

    @property
    def is_attacking(self):
        return self.attack_frame > 0