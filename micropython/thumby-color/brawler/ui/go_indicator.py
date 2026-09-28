# ui/go_indicator.py
# Phase 08: "GO! ▶" Directional UI Indicator
# Blinking screen edge indicator to guide player to the next stage area.

class GoIndicator:
    def __init__(self, screen_width=128, screen_height=128):
        self.screen_w = screen_width
        self.screen_h = screen_height
        
        # Animation config (30 FPS sync)
        self.blink_interval = 12   # Toggle state every 12 frames (~0.4s)
        self.frame_counter = 0
        self.visible = True
        
        # Visual Position (Right edge centered)
        self.x = self.screen_w - 28
        self.y = 16

    def update(self, is_active):
        """
        Update blink animation timer.
        Call every frame when stage_manager.show_go_indicator is True.
        """
        if not is_active:
            self.frame_counter = 0
            self.visible = True
            return

        self.frame_counter += 1
        if self.frame_counter >= self.blink_interval:
            self.frame_counter = 0
            self.visible = not self.visible

    def draw(self, display, is_active):
        """
        Render the blinking 'GO! >' indicator on Thumby Color display.
        Assumes standard MicroPython display interface or SSD1306/RGB canvas.
        """
        if not is_active or not self.visible:
            return

        # Simple text or bitmap arrow rendering
        # Text string fits within 128x128 resolution bounds
        if hasattr(display, 'text'):
            # (text, x, y, color)
            display.text("GO! >", self.x, self.y, 0xFFFF)