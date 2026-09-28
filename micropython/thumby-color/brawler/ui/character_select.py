# ui/character_select.py
# Phase 12 Asset Polish: 3-Step Hero Customization Menu
# Step 1: Gender (MALE/FEMALE)
# Step 2: Outfit (Joseon/Wushu/Ronin)
# Step 3: Costume Color (7 Traditional Presets)

import thumby
from data.character_presets import (
    COMMON_HERO_STATS,
    GENDER_OPTIONS,
    OUTFIT_OPTIONS,
    PALETTE_PRESETS
)

class CharacterSelectUI:
    STEP_GENDER = 0
    STEP_OUTFIT = 1
    STEP_PALETTE = 2

    def __init__(self, screen_w=128, screen_h=128):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.active = False
        
        self.current_step = self.STEP_GENDER
        self.gender_idx = 0
        self.outfit_idx = 0
        self.palette_idx = 0

    def open_select(self):
        """Activates character customization flow."""
        self.active = True
        self.current_step = self.STEP_GENDER
        self.gender_idx = 0
        self.outfit_idx = 0
        self.palette_idx = 0

    def handle_input(self, button_left, button_right, button_a, button_b):
        """
        DPAD Left/Right to change selection at current step.
        Button A to confirm step.
        Button B to go back to previous step.
        Returns final build dict when all 3 steps complete, else None.
        """
        if not self.active:
            return None

        # B Button: Go back step or exit
        if button_b:
            if self.current_step > self.STEP_GENDER:
                self.current_step -= 1
                return None

        # Step 1: Gender Selection
        if self.current_step == self.STEP_GENDER:
            if button_left or button_right:
                self.gender_idx = (self.gender_idx + 1) % len(GENDER_OPTIONS)
            if button_a:
                self.current_step = self.STEP_OUTFIT

        # Step 2: Outfit/Culture Selection
        elif self.current_step == self.STEP_OUTFIT:
            if button_left:
                self.outfit_idx = (self.outfit_idx - 1) % len(OUTFIT_OPTIONS)
            elif button_right:
                self.outfit_idx = (self.outfit_idx + 1) % len(OUTFIT_OPTIONS)
            if button_a:
                self.current_step = self.STEP_PALETTE

        # Step 3: Palette Selection & Confirmation
        elif self.current_step == self.STEP_PALETTE:
            if button_left:
                self.palette_idx = (self.palette_idx - 1) % len(PALETTE_PRESETS)
            elif button_right:
                self.palette_idx = (self.palette_idx + 1) % len(PALETTE_PRESETS)
            if button_a:
                self.active = False
                return self.get_final_hero_config()

        return None

    def get_final_hero_config(self):
        """Returns assembled customization dictionary for Player initialization."""
        selected_gender = GENDER_OPTIONS[self.gender_idx]
        selected_outfit = OUTFIT_OPTIONS[self.outfit_idx]
        selected_palette = PALETTE_PRESETS[self.palette_idx]

        return {
            "gender": selected_gender["id"],
            "outfit": selected_outfit["id"],
            "color": selected_palette["color"],
            "color_name": selected_palette["name"],
            "hat_style": selected_outfit["hat_m"] if selected_gender["id"] == "MALE" else selected_outfit["hat_f"],
            "stats": COMMON_HERO_STATS
        }

    def draw(self, display):
        """Renders 128x128 3-Step Character Creation Screen."""
        if not self.active:
            return

        gender = GENDER_OPTIONS[self.gender_idx]
        outfit = OUTFIT_OPTIONS[self.outfit_idx]
        palette = PALETTE_PRESETS[self.palette_idx]

        # Border
        if hasattr(display, 'fill_rect'):
            display.fill_rect(0, 0, self.screen_w, self.screen_h, 0x0000)
            display.rect(4, 4, 120, 120, 0xFFFF)
            display.rect(6, 6, 116, 116, 0xFFE0)

        if hasattr(display, 'text'):
            # Step Title Header
            step_titles = ["1/3 GENDER", "2/3 OUTFIT", "3/3 PALETTE"]
            display.text(step_titles[self.current_step], 24, 12, 0xFFE0)

            # Interactive Options Preview
            display.text("<", 10, 32, 0xFFFF)
            display.text(">", 112, 32, 0xFFFF)

            if self.current_step == self.STEP_GENDER:
                display.text(gender["label"], 36, 32, 0xFFFF)
            elif self.current_step == self.STEP_OUTFIT:
                display.text(outfit["name"], 20, 32, 0xFFFF)
            elif self.current_step == self.STEP_PALETTE:
                display.text(palette["name"][:13], 16, 32, palette["color"])

            # Center SD Preview Box
            box_x, box_y = 56, 48
            if hasattr(display, 'rect'):
                display.rect(box_x - 2, box_y - 2, 20, 24, 0xFFFF)
                
                # Render Robe with Selected Color Palette
                display.fill_rect(box_x + 3, box_y + 8, 10, 7, palette["color"])
                # Render Skin (Face)
                display.fill_rect(box_x + 4, box_y + 3, 8, 5, 0xFBE0)

            # Details
            hat_text = outfit["hat_m"] if gender["id"] == "MALE" else outfit["hat_f"]
            display.text(f"Style: {hat_text[:12]}", 12, 80, 0xFFE0)
            display.text(f"Culture: {outfit['id']}", 12, 92, 0xFFFF)

            # Navigation Footer
            display.text("[A]NEXT  [B]BACK", 12, 108, 0x07E0)