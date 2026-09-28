# engine/progression.py
# Phase 11: Progression State & Stage Transition Engine
# Coordinates auto-save triggers, stage clear flows, and Game Over retries.

from engine.save_manager import SaveManager

class ProgressionEngine:
    # Game Flow States
    STATE_PLAYING = 0
    STATE_STAGE_CLEAR = 1
    STATE_GAME_OVER = 2

    def __init__(self, start_stage_idx=1):
        self.current_stage_idx = start_stage_idx
        self.state = self.STATE_PLAYING
        self.clear_banner_timer = 0

    def init_from_save(self, player):
        """Loads persistent progress from flash and initializes player state."""
        save_data = SaveManager.load_game(player)
        self.current_stage_idx = save_data.get("stage_index", 1)
        self.state = self.STATE_PLAYING

    def on_shop_close(self, player):
        """Auto-saves when exiting the Town Shop."""
        SaveManager.save_game(player, self.current_stage_idx)

    def trigger_stage_clear(self, player):
        """Triggers stage clear sequence, increments stage index, and auto-saves."""
        self.state = self.STATE_STAGE_CLEAR
        self.clear_banner_timer = 90  # 3 seconds display at 30 FPS
        self.current_stage_idx += 1
        
        # Save progress after clearing stage
        SaveManager.save_game(player, self.current_stage_idx)

    def trigger_game_over(self):
        """Triggers Game Over state."""
        self.state = self.STATE_GAME_OVER

    def retry_stage(self, player):
        """Restores player stats from last saved checkpoint on retry."""
        save_data = SaveManager.load_game(player)
        self.state = self.STATE_PLAYING
        return save_data.get("stage_index", 1)

    def update(self):
        """Updates progression timers."""
        if self.state == self.STATE_STAGE_CLEAR and self.clear_banner_timer > 0:
            self.clear_banner_timer -= 1

    def draw_status_overlay(self, display):
        """Renders Stage Clear / Game Over banner overlays on 128x128 screen."""
        if self.state == self.STATE_STAGE_CLEAR and self.clear_banner_timer > 0:
            if hasattr(display, 'fill_rect'):
                display.fill_rect(10, 48, 108, 32, 0x0000)
                display.rect(10, 48, 108, 32, 0xFFE0)  # Gold Border
            if hasattr(display, 'text'):
                display.text("STAGE CLEAR!", 18, 54, 0xFFE0)
                display.text("Progress Saved", 14, 66, 0xFFFF)

        elif self.state == self.STATE_GAME_OVER:
            if hasattr(display, 'fill_rect'):
                display.fill_rect(10, 44, 108, 40, 0x0000)
                display.rect(10, 44, 108, 40, 0xF800)  # Red Border
            if hasattr(display, 'text'):
                display.text("GAME OVER", 28, 50, 0xF800)
                display.text("[A] Retry Stage", 12, 66, 0xFFFF)