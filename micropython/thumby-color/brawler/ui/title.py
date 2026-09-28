# ui/title.py
# Phase 12: Title Screen & Game State Manager
# Handles Main Title UI, New Game, and Save State Continuation.

import thumby
from engine.save_manager import SaveManager, SAVE_FILE_PATH

class TitleUI:
    def __init__(self, screen_w=128, screen_h=128):
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        self.active = True
        self.selected_index = 0  # 0: NEW GAME, 1: CONTINUE
        self.has_save = False
        self.check_save_file()

    def check_save_file(self):
        """Checks if a valid save file exists on Flash storage."""
        try:
            with open(SAVE_FILE_PATH, "r") as f:
                self.has_save = True
        except (OSError, ValueError):
            self.has_save = False
            self.selected_index = 0

    def handle_input(self, button_up, button_down, button_a):
        """
        Handles DPAD navigation and game launch triggers.
        Returns 'NEW_GAME', 'CONTINUE', or None.
        """
        if not self.active:
            return None

        # Navigation
        if button_up or button_down:
            if self.has_save:
                self.selected_index = 1 - self.selected_index

        # Confirm Selection (A button)
        if button_a:
            self.active = False
            if self.selected_index == 0:
                return "NEW_GAME"
            elif self.selected_index == 1 and self.has_save:
                return "CONTINUE"

        return None

    def draw(self, display):
        """Renders 128x128 Retro Title Screen."""
        if not self.active:
            return

        # Background Frame
        if hasattr(display, 'fill_rect'):
            display.fill_rect(0, 0, self.screen_w, self.screen_h, 0x0000)
            display.rect(4, 4, 120, 120, 0xFFFF)
            display.rect(6, 6, 116, 116, 0xFFE0)  # Inner Gold Line

        if hasattr(display, 'text'):
            # Title Banner
            display.text("STREET BRAWLER", 12, 24, 0xFFE0)
            display.text("~ PERIOD ACTION ~", 8, 36, 0xFFFF)

            # Menu Options
            c1 = ">" if self.selected_index == 0 else " "
            col1 = 0xFFE0 if self.selected_index == 0 else 0xFFFF
            display.text(f"{c1} NEW GAME", 28, 68, col1)

            c2 = ">" if self.selected_index == 1 else " "
            col2 = 0xFFE0 if self.selected_index == 1 else (0xFFFF if self.has_save else 0x8410)
            cont_str = "  CONTINUE" if not self.has_save else f"{c2} CONTINUE"
            display.text(cont_str, 28, 82, col2)

            # Control Footer
            display.text("[A] START", 36, 106, 0x07E0)