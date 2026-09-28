import random

class Camera:
    def __init__(self, world_width=512, viewport_width=128):
        self.x = 0.0
        self.world_width = world_width
        self.viewport_width = viewport_width
        self.deadzone_left = 48
        self.deadzone_right = 80
        
        # Camera Shake parameters
        self.shake_intensity = 0.0
        self.shake_offset_x = 0
        self.shake_offset_y = 0

    def add_shake(self, intensity=4.0):
        self.shake_intensity = max(self.shake_intensity, intensity)

    def update(self, player_x):
        # Base Camera Deadzone Tracking
        screen_x = player_x - self.x
        if screen_x < self.deadzone_left:
            self.x = player_x - self.deadzone_left
        elif screen_x > self.deadzone_right:
            self.x = player_x - self.deadzone_right

        self.x = max(0.0, min(float(self.world_width - self.viewport_width), self.x))

        # Calculate Camera Shake Decay
        if self.shake_intensity > 0.1:
            self.shake_offset_x = int((random.random() * 2 - 1) * self.shake_intensity)
            self.shake_offset_y = int((random.random() * 2 - 1) * self.shake_intensity)
            self.shake_intensity *= 0.75  # Fast decay curve
        else:
            self.shake_intensity = 0.0
            self.shake_offset_x = 0
            self.shake_offset_y = 0