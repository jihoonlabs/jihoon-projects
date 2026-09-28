# ui/stage_branch.py
# Phase 12 Overseas Expedition Branch UI: Path Selection after Stage Clear

import thumby

class StageBranchUI:
    def __init__(self, screen_w=128, screen_h=128):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.active = False
        self.choices = []
        self.selected_idx = 0

    def open_branch(self, available_choices):
        """Activates branch selection menu with available overseas stage choices."""
        self.choices = available_choices
        self.selected_idx = 0
        self.active = True

    def handle_input(self, button_up, button_down, button_a):
        """
        DPAD Up/Down to navigate choices.
        Button A to confirm chosen expedition path.
        Returns selected stage dictionary or None.
        """
        if not self.active or not self.choices:
            return None

        if button_up:
            self.selected_idx = (self.selected_idx - 1) % len(self.choices)
        elif button_down:
            self.selected_idx = (self.selected_idx + 1) % len(self.choices)

        if button_a:
            self.active = False
            return self.choices[self.selected_idx]

        return None

    def draw(self, display):
        """Renders 128x128 Expedition Branch Screen."""
        if not self.active:
            return

        # Background overlay
        if hasattr(display, 'fill_rect'):
            display.fill_rect(0, 0, self.screen_w, self.screen_h, 0x0000)
            display.rect(4, 4, 120, 120, 0xFFFF)
            display.rect(6, 6, 116, 116, 0xFFE0)

        if hasattr(display, 'text'):
            # Header
            display.text("OVERSEAS PATH", 16, 12, 0xFFE0)
            display.text("Choose Expedition", 8, 24, 0xFFFF)

            # Option List
            start_y = 44
            for i, choice in enumerate(self.choices):
                y_pos = start_y + (i * 22)
                is_selected = (i == self.selected_idx)
                
                # Selection Cursor highlight
                prefix = "> " if is_selected else "  "
                color = 0x07E0 if is_selected else 0xFFFF

                if is_selected and hasattr(display, 'fill_rect'):
                    display.fill_rect(10, y_pos - 2, 108, 18, 0x1082)

                display.text(f"{prefix}{choice['title'][:12]}", 12, y_pos, color)
                display.text(f"  Region: {choice['id']}", 12, y_pos + 9, 0xFFE0)

            # Navigation Footer
            display.text("[UP/DN]Move [A]Sail", 8, 108, 0x07E0)