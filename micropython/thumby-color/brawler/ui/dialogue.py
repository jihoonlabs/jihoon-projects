# ui/dialogue.py
# Phase 08: Lightweight Dialogue UI Engine
# Compact typewriter box renderer optimized for 128x128 MicroPython display.

class DialogueUI:
    def __init__(self, screen_width=128, screen_height=128):
        self.screen_w = screen_width
        self.screen_h = screen_height
        
        # UI Box Dimensions (Bottom overlay)
        self.box_h = 36
        self.box_y = self.screen_h - self.box_h
        
        # Dialogue State
        self.active = False
        self.dialogue_list = []
        self.current_index = 0
        
        # Typewriter Animation Controls (30 FPS)
        self.char_index = 0
        self.ticks_per_char = 2  # Render 1 character every 2 frames
        self.tick_counter = 0
        self.text_complete = False

    def start_dialogue(self, dialogue_data):
        """Initializes dialogue sequence with input data list."""
        if not dialogue_data:
            return
            
        self.dialogue_list = dialogue_data
        self.current_index = 0
        self.active = True
        self._reset_typewriter()

    def _reset_typewriter(self):
        self.char_index = 0
        self.tick_counter = 0
        self.text_complete = False

    def handle_input(self, button_a_pressed):
        """
        Handles A-button press.
        1st Press: Instantly complete typing current line.
        2nd Press: Advance to next line or exit dialogue.
        """
        if not self.active or not button_a_pressed:
            return

        current_stanza = self.dialogue_list[self.current_index]
        full_text = current_stanza.get("text", "")

        if not self.text_complete:
            # Skip typing animation, show full line
            self.char_index = len(full_text)
            self.text_complete = True
        else:
            # Advance to next dialogue stanza
            self.current_index += 1
            if self.current_index >= len(self.dialogue_list):
                # End of dialogue
                self.active = False
            else:
                self._reset_typewriter()

    def update(self):
        """Updates typewriter text character index."""
        if not self.active or self.text_complete:
            return

        current_stanza = self.dialogue_list[self.current_index]
        full_text = current_stanza.get("text", "")

        self.tick_counter += 1
        if self.tick_counter >= self.ticks_per_char:
            self.tick_counter = 0
            self.char_index += 1

            if self.char_index >= len(full_text):
                self.char_index = len(full_text)
                self.text_complete = True

    def draw(self, display):
        """Draws dialogue box, speaker name, text and advance indicator."""
        if not self.active:
            return

        current_stanza = self.dialogue_list[self.current_index]
        speaker = current_stanza.get("speaker", "???")
        full_text = current_stanza.get("text", "")
        displayed_text = full_text[:self.char_index]

        # 1. Background Box (Solid Dark background)
        if hasattr(display, 'fill_rect'):
            display.fill_rect(0, self.box_y, self.screen_w, self.box_h, 0x0000)
            display.rect(0, self.box_y, self.screen_w, self.box_h, 0xFFFF)

        # 2. Speaker Label
        if hasattr(display, 'text'):
            display.text(f"[{speaker}]", 4, self.box_y + 4, 0xFFE0) # Yellow / Accent color
            display.text(displayed_text, 4, self.box_y + 16, 0xFFFF)

            # 3. Next Indicator (Blinking prompt when typing is complete)
            if self.text_complete and (self.tick_counter // 8) % 2 == 0:
                display.text("v", self.screen_w - 10, self.screen_h - 10, 0xFFFF)