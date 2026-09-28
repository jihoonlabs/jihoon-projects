import thumby
from entities.base import Entity
from engine.physics import DoubleTapDetector, JumpPhysics

COLOR_PLAYER = 0x07E0
COLOR_PLAYER_DASH = 0xFFE0

class Player(Entity):
    def __init__(self, x=40, y=80):
        super().__init__('player', x, y, z=0.0, w=12, h=16, color=COLOR_PLAYER)
        self.vz = 0.0
        self.walk_speed = 1.6
        self.dash_speed = 2.8
        self.is_jumping = False
        self.is_dashing = False
        
        self.double_tap = DoubleTapDetector()
        self.jump_physics = JumpPhysics()

    def update(self, world_width=512):
        # 1. Dash Input
        if thumby.buttonL.justPressed():
            if self.double_tap.check('L'): self.is_dashing = True
        elif thumby.buttonR.justPressed():
            if self.double_tap.check('R'): self.is_dashing = True

        if not (thumby.buttonL.pressed() or thumby.buttonR.pressed() or thumby.buttonU.pressed() or thumby.buttonD.pressed()):
            self.is_dashing = False

        # 2. Movement
        move_x, move_y = 0, 0
        if thumby.buttonL.pressed(): move_x -= 1
        if thumby.buttonR.pressed(): move_x += 1
        if thumby.buttonU.pressed(): move_y -= 1
        if thumby.buttonD.pressed(): move_y += 1

        speed = self.dash_speed if self.is_dashing else self.walk_speed
        self.x += move_x * speed
        self.y += move_y * (speed * 0.65)

        # Boundaries
        self.x = max(8.0, min(float(world_width - 16), self.x))
        self.y = max(58.0, min(112.0, self.y))

        # 3. Jump Input & Physics
        if thumby.buttonB.justPressed() and not self.is_jumping:
            self.is_jumping = True
            self.vz = self.jump_physics.jump_force

        self.z, self.vz, self.is_jumping = self.jump_physics.update(self.z, self.vz, self.is_jumping)

        # Color feedback
        self.color = COLOR_PLAYER_DASH if self.is_dashing else COLOR_PLAYER

    @property
    def state_str(self):
        if self.is_jumping: return "JUMP"
        if self.is_dashing: return "DASH"
        return "WALK"