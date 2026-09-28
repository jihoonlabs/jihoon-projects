# gfx/telegraph.py
# Phase 09: Telegraphed Attack Warning Visualizer
# Renders warning hazard indicators (RGB565 red outline/fill) during Boss startup frames.

class TelegraphVisualizer:
    def __init__(self):
        # RGB565 Colors for Thumby Color Display
        self.COLOR_WARNING_RED = 0xF800
        self.COLOR_WARNING_ORANGE = 0xFD20
        self.blink_interval = 4  # Fast blink every 4 frames (~0.13s at 30 FPS)

    def draw_boss_telegraph(self, display, camera, boss):
        """
        Renders warning box on display based on Boss current skill telegraph spec.
        Call inside main renderer loop when boss is in STATE_TELEGRAPH.
        """
        if getattr(boss, 'state', None) != 2:  # STATE_TELEGRAPH = 2
            return

        skill = getattr(boss, 'current_skill', None)
        if not skill or "telegraph_box" not in skill:
            return

        t_box = skill["telegraph_box"]
        
        # Calculate Screen Coordinates considering Camera offset
        world_box_x = boss.x + (t_box["offset_x"] if boss.facing == 1 else -t_box["offset_x"] - t_box["width"])
        world_box_y = boss.y + t_box["offset_y"]
        
        screen_x = int(world_box_x - camera.x)
        screen_y = int(world_box_y)
        w = t_box["width"]
        h = t_box["height"]

        # Fast Blinking Animation during Startup Frames
        timer = getattr(boss, 'skill_timer', 0)
        is_blink_frame = (timer // self.blink_interval) % 2 == 0
        color = self.COLOR_WARNING_RED if is_blink_frame else self.COLOR_WARNING_ORANGE

        # Render Warning Box on Thumby Color Display
        if hasattr(display, 'rect'):
            display.rect(screen_x, screen_y, w, h, color)
            
            # Draw inner diagonal cross for critical attacks (e.g. GROUND_SLAM)
            if skill.get("damage", 0) >= 20 and is_blink_frame:
                display.line(screen_x, screen_y, screen_x + w, screen_y + h, color)
                display.line(screen_x + w, screen_y, screen_x, screen_y + h, color)