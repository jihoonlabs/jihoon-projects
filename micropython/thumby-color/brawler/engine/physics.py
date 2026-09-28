import time

class DoubleTapDetector:
    def __init__(self, gap_ms=300):
        self.gap_ms = gap_ms
        self.last_press_time = 0
        self.last_btn = None

    def check(self, btn_name):
        now = time.ticks_ms()
        is_double = (self.last_btn == btn_name) and (time.ticks_diff(now, self.last_press_time) < self.gap_ms)
        self.last_press_time = now
        self.last_btn = btn_name
        return is_double

class JumpPhysics:
    def __init__(self, gravity=0.38, jump_force=-4.2):
        self.gravity = gravity
        self.jump_force = jump_force

    def update(self, z, vz, is_jumping):
        if not is_jumping:
            return z, vz, False

        z += vz
        vz += self.gravity

        if z >= 0:
            z = 0.0
            vz = 0.0
            is_jumping = False

        return z, vz, is_jumping