class Camera:
    def __init__(self, world_width=512, deadzone_left=48, deadzone_right=80):
        self.x = 0.0
        self.world_width = world_width
        self.deadzone_left = deadzone_left
        self.deadzone_right = deadzone_right

    def update(self, target_x):
        screen_x = target_x - self.x
        if screen_x > self.deadzone_right:
            self.x += (screen_x - self.deadzone_right)
        elif screen_x < self.deadzone_left:
            self.x -= (self.deadzone_left - screen_x)

        # Stage Boundary Clamp
        self.x = max(0.0, min(float(self.world_width - 128), self.x))