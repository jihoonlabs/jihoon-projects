import time
import gc

class DebugManager:
    def __init__(self):
        # Debug Level: 0 = Off, 1 = HUD Telemetry, 2 = Wireframe Hitboxes
        self.level = 1
        self.god_mode = False
        self.fps = 30.0
        self.last_time = time.ticks_ms()
        self.frame_count = 0
        self.fps_timer = time.ticks_ms()

    def toggle_level(self):
        self.level = (self.level + 1) % 3

    def toggle_god_mode(self):
        self.god_mode = not self.god_mode

    def update_telemetry(self):
        now = time.ticks_ms()
        self.frame_count += 1
        diff = time.ticks_diff(now, self.fps_timer)

        if diff >= 500:  # Update FPS every 0.5s
            self.fps = (self.frame_count * 1000.0) / diff
            self.frame_count = 0
            self.fps_timer = now

    @property
    def free_mem_kb(self):
        return gc.mem_free() // 1024