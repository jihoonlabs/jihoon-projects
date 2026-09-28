# engine/audio.py
# Phase 12: Non-blocking Audio Sound Engine for Thumby Color Piezo Buzzer
# Handles 8-bit sound effects and chiptune audio cues without blocking the 30 FPS main loop.

import thumby

class AudioEngine:
    def __init__(self):
        self.current_note_frames = 0
        self.muted = False

    def update(self):
        """
        Main tick method called every frame (30 FPS).
        Stops active buzzer tones when duration expires.
        """
        if self.current_note_frames > 0:
            self.current_note_frames -= 1
            if self.current_note_frames <= 0:
                thumby.audio.stop()

    def _play_tone(self, freq_hz, duration_ms):
        """Helper to trigger buzzer tone with non-blocking frame timer."""
        if self.muted:
            return
        
        try:
            thumby.audio.play(int(freq_hz), int(duration_ms))
            # Calculate frame duration (30 FPS -> ~33.3ms per frame)
            self.current_note_frames = max(1, int(duration_ms / 33))
        except Exception:
            pass

    # ----------------------------------------------------
    # Brawler Sound Effects (SFX Presets)
    # ----------------------------------------------------
    def play_sfx_punch(self):
        """Light hit / Punch sound."""
        self._play_tone(180, 45)

    def play_sfx_slash(self):
        """Sword slash impact sound."""
        self._play_tone(420, 60)

    def play_sfx_gunshot(self):
        """Matchlock / Handgun shooting recoil sound."""
        self._play_tone(90, 80)

    def play_sfx_coin(self):
        """Coin pickup / Item collect chime."""
        self._play_tone(988, 70)  # High B5 note

    def play_sfx_skill(self):
        """Special skill scroll execution sound."""
        self._play_tone(659, 90)  # E5 note

    def play_sfx_boss_roar(self):
        """Boss phase transition / Super armor cue."""
        self._play_tone(120, 150)

    def play_sfx_game_over(self):
        """Game Over death tone."""
        self._play_tone(150, 250)