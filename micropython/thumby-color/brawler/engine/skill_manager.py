# engine/skill_manager.py
# Phase 10: Skill Scroll Manager & Command Binding System
# Maps purchased skill scrolls to directional button combinations. Zero GC allocation.

class SkillManager:
    # Skill Scroll Specifications
    SKILL_PRESETS = {
        "SWEEP_KICK": {
            "name": "Sweep Kick Scroll",
            "cmd": "DOWN_B",           # Triggered via Down + B
            "damage": 18,
            "hitbox_w": 22,
            "hitbox_h": 6,             # Low ground attack box
            "cooldown_frames": 20,
            "knockback_x": 10,
            "stun_frames": 15,
            "description": "Low ground sweep kick that trips enemies."
        },
        "UPPERCUT": {
            "name": "Rising Uppercut",
            "cmd": "UP_B",             # Triggered via Up + B
            "damage": 22,
            "hitbox_w": 18,
            "hitbox_h": 24,            # Vertical high hit box
            "cooldown_frames": 25,
            "knockback_x": 4,
            "stun_frames": 20,
            "description": "High vertical strike sending enemies airborne."
        },
        "FLURRY_PUNCH": {
            "name": "Hundred Fists",
            "cmd": "FORWARD_B",        # Triggered via Forward + B
            "damage": 28,
            "hitbox_w": 30,
            "hitbox_h": 14,
            "cooldown_frames": 35,
            "knockback_x": 14,
            "stun_frames": 25,
            "description": "Rapid punch flurry pushing back targets."
        }
    }

    def __init__(self):
        # List of skill scroll IDs learned by the player
        self.unlocked_skills = []
        self.cooldown_timer = 0

    def learn_skill(self, skill_id):
        """
        Unlocks a new skill scroll purchased from Town Shop.
        """
        if skill_id in self.SKILL_PRESETS and skill_id not in self.unlocked_skills:
            self.unlocked_skills.append(skill_id)
            return True
        return False

    def update(self):
        """Decrements skill cooldown frame counter (30 FPS sync)."""
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

    def check_skill_trigger(self, dpad_dir, button_b_pressed):
        """
        Checks if current D-Pad directional state + B-button matches an unlocked skill command.
        - dpad_dir: "DOWN", "UP", "FORWARD", or "NEUTRAL"
        - button_b_pressed: True on frame B is pressed
        Returns matched skill spec or None.
        """
        if not button_b_pressed or self.cooldown_timer > 0:
            return None

        # Determine input string
        cmd_str = f"{dpad_dir}_B"

        for skill_id in self.unlocked_skills:
            spec = self.SKILL_PRESETS.get(skill_id)
            if spec and spec["cmd"] == cmd_str:
                self.cooldown_timer = spec["cooldown_frames"]
                return spec

        return None