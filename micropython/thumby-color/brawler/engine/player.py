import thumby
from entities.base import Entity
from engine.physics import DoubleTapDetector, JumpPhysics
from engine.hitbox import VolumeHitbox

COLOR_PLAYER = 0x07E0
COLOR_PLAYER_DASH = 0xFFE0
COLOR_PLAYER_ATTACK = 0xF81F

class Player(Entity):
    def __init__(self, x=40, y=80):
        super().__init__('player', x, y, z=0.0, w=12, h=16, color=COLOR_PLAYER)
        self.vz = 0.0
        self.walk_speed = 1.6
        self.dash_speed = 2.8
        self.is_jumping = False
        self.is_dashing = False

        # Attack & Active Frame System
        self.attack_frame = 0
        self.max_attack_frames = 6
        self.hitbox = VolumeHitbox(self, range_x=16, depth_y=8, height_z=12, damage=15, knockback_x=4.0, hitstun_frames=10)

        self.double_tap = DoubleTapDetector()
        self.jump_physics = JumpPhysics()

    def update(self, world_width=512):
        # 0. Apply Hitstun & Knockback Friction
        self.update_physics()
        if self.hitstun > 0:
            return  # Lock input during hitstun

        # 1. Attack Trigger (Button A)
        if thumby.buttonA.justPressed() and self.attack_frame == 0 and not self.is_jumping:
            self.attack_frame = self.max_attack_frames

        if self.attack_frame > 0:
            self.attack_frame -= 1
            self.color = COLOR_PLAYER_ATTACK
            return  # Lock movement during attack swing

        # 2. Dash Input
        if thumby.buttonL.justPressed():
            if self.double_tap.check('L'): self.is_dashing = True
        elif thumby.buttonR.justPressed():
            if self.double_tap.check('R'): self.is_dashing = True

        if not (thumby.buttonL.pressed() or thumby.buttonR.pressed() or thumby.buttonU.pressed() or thumby.buttonD.pressed()):
            self.is_dashing = False

        # 3. Direction & Movement
        move_x, move_y = 0, 0
        if thumby.buttonL.pressed(): 
            move_x -= 1
            self.facing_right = False
        if thumby.buttonR.pressed(): 
            move_x += 1
            self.facing_right = True
        if thumby.buttonU.pressed(): move_y -= 1
        if thumby.buttonD.pressed(): move_y += 1

        speed = self.dash_speed if self.is_dashing else self.walk_speed
        self.x += move_x * speed
        self.y += move_y * (speed * 0.65)

        # Boundaries
        self.x = max(8.0, min(float(world_width - 16), self.x))
        self.y = max(58.0, min(112.0, self.y))

        # 4. Jump
        if thumby.buttonB.justPressed() and not self.is_jumping:
            self.is_jumping = True
            self.vz = self.jump_physics.jump_force

        self.z, self.vz, self.is_jumping = self.jump_physics.update(self.z, self.vz, self.is_jumping)

        # State Color
        self.color = COLOR_PLAYER_DASH if self.is_dashing else COLOR_PLAYER

    @property
    def is_attacking(self):
        return self.attack_frame > 0

    @property
    def state_str(self):
        if self.hitstun > 0: return "HIT"
        if self.is_attacking: return "ATK"
        if self.is_jumping: return "JUMP"
        if self.is_dashing: return "DASH"
        return "WALK"