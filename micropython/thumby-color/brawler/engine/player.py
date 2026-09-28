import thumby
from entities.base import Entity
from engine.physics import DoubleTapDetector, JumpPhysics
from engine.hitbox import VolumeHitbox

COLOR_PLAYER = 0x07E0
COLOR_PLAYER_DASH = 0xFFE0
COLOR_ATK1 = 0xFFE0
COLOR_ATK2 = 0xFD20
COLOR_FINISHER = 0xF800
COLOR_SPECIAL = 0x07FF

class Player(Entity):
    def __init__(self, x=40, y=80):
        super().__init__('player', x, y, z=0.0, w=12, h=16, color=COLOR_PLAYER)
        self.vz = 0.0
        self.walk_speed = 1.6
        self.dash_speed = 2.8
        self.is_jumping = False
        self.is_dashing = False

        # Combo Engine
        self.combo_step = 0          # 0: None, 1: Atk1, 2: Atk2, 3: Finisher
        self.combo_timer = 0         # Combo window countdown
        self.combo_buffer = False    # Buffer next attack press
        self.is_special = False      # AoE Skill flag

        self.hitbox = None
        self.double_tap = DoubleTapDetector()
        self.jump_physics = JumpPhysics()

    def trigger_attack(self, step):
        self.combo_step = step
        self.combo_buffer = False

        if step == 1:
            self.combo_timer = 12
            self.color = COLOR_ATK1
            self.hitbox = VolumeHitbox(self, range_x=14, depth_y=8, height_z=12, damage=8, knockback_x=2.0, hitstun_frames=6)
        elif step == 2:
            self.combo_timer = 12
            self.color = COLOR_ATK2
            self.hitbox = VolumeHitbox(self, range_x=16, depth_y=8, height_z=12, damage=12, knockback_x=3.0, hitstun_frames=8)
        elif step == 3: # Finisher
            self.combo_timer = 16
            self.color = COLOR_FINISHER
            self.hitbox = VolumeHitbox(self, range_x=20, depth_y=10, height_z=14, damage=22, knockback_x=6.5, hitstun_frames=16)

    def trigger_special(self):
        if self.hp > 10:
            self.hp -= 10  # Consumes HP
            self.is_special = True
            self.combo_step = 4
            self.combo_timer = 18
            self.color = COLOR_SPECIAL
            # Radial 360-degree Hitbox
            self.hitbox = VolumeHitbox(self, range_x=24, depth_y=16, height_z=16, damage=30, knockback_x=8.0, hitstun_frames=20)

    def update(self, world_width=512):
        self.update_physics()
        if self.hitstun > 0:
            self.combo_step = 0
            return

        # 1. Emergency AoE Special Trigger (Button A + B)
        if thumby.buttonA.pressed() and thumby.buttonB.pressed() and self.combo_step == 0:
            self.trigger_special()
            return

        # 2. Combo Processing & Input Buffering
        if self.combo_step > 0:
            if thumby.buttonA.justPressed():
                self.combo_buffer = True

            self.combo_timer -= 1
            if self.combo_timer <= 0:
                # Execute Next Combo Stage if buffered
                if self.combo_buffer and self.combo_step < 3 and not self.is_special:
                    self.trigger_attack(self.combo_step + 1)
                else:
                    # Reset Combo State
                    self.combo_step = 0
                    self.combo_buffer = False
                    self.is_special = False
                    self.hitbox = None
            return

        # 3. Base Combo Trigger (Button A)
        if thumby.buttonA.justPressed() and not self.is_jumping:
            self.trigger_attack(1)
            return

        # 4. Movement
        if thumby.buttonL.justPressed():
            if self.double_tap.check('L'): self.is_dashing = True
        elif thumby.buttonR.justPressed():
            if self.double_tap.check('R'): self.is_dashing = True

        if not (thumby.buttonL.pressed() or thumby.buttonR.pressed() or thumby.buttonU.pressed() or thumby.buttonD.pressed()):
            self.is_dashing = False

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

        self.x = max(8.0, min(float(world_width - 16), self.x))
        self.y = max(58.0, min(112.0, self.y))

        # 5. Jump
        if thumby.buttonB.justPressed() and not self.is_jumping:
            self.is_jumping = True
            self.vz = self.jump_physics.jump_force

        self.z, self.vz, self.is_jumping = self.jump_physics.update(self.z, self.vz, self.is_jumping)
        self.color = COLOR_PLAYER_DASH if self.is_dashing else COLOR_PLAYER

    @property
    def is_attacking(self):
        return self.combo_step > 0

    @property
    def state_str(self):
        if self.hitstun > 0: return "HIT"
        if self.is_special: return "AOE!"
        if self.combo_step == 1: return "ATK1"
        if self.combo_step == 2: return "ATK2"
        if self.combo_step == 3: return "FINISH"
        if self.is_jumping: return "JUMP"
        if self.is_dashing: return "DASH"
        return "WALK"