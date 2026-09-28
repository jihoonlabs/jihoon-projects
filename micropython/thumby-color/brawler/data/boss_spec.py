# data/boss_spec.py
# Phase 09: Data-Driven Boss Specifications
# Lightweight dictionary structure optimized for RP2040 MicroPython

BOSS_GENERAL_01_SPEC = {
    "boss_id": "boss_general_01",
    "title": "Bandit Leader",
    "max_hp": 150,
    "move_speed": 1.2,
    "y_alignment_speed": 0.8,
    "weight_class": "HEAVY",  # Higher resistance to base knockback
    
    # Phase 2 Transition Trigger (<= 50% HP)
    "phase_2_hp_threshold": 0.5,
    "phase_2_speed_multiplier": 1.3,
    "phase_2_aura_color": 0xF800,  # Red glow aura (RGB565)

    # Attack Skill Patterns
    "skills": {
        "HEAVY_SLASH": {
            "damage": 15,
            "startup_frames": 18,     # Telegraph warning duration (0.6 sec)
            "active_frames": 6,
            "recovery_frames": 20,
            "super_armor": True,      # Immune to hitstun during attack
            "knockback_x": 8,
            "telegraph_box": {"offset_x": 10, "offset_y": -8, "width": 24, "height": 16}
        },
        "GROUND_SLAM": {
            "damage": 25,
            "startup_frames": 24,     # Telegraph warning duration (0.8 sec)
            "active_frames": 8,
            "recovery_frames": 30,
            "super_armor": True,
            "knockback_x": 12,
            "telegraph_box": {"offset_x": -15, "offset_y": -15, "width": 30, "height": 30}
        }
    },

    # AI Pattern Selection Probabilities
    "patterns": {
        "PHASE_1": [
            {"skill": "HEAVY_SLASH", "weight": 70, "cooldown_frames": 45},
            {"skill": "GROUND_SLAM", "weight": 30, "cooldown_frames": 90}
        ],
        "PHASE_2": [
            {"skill": "HEAVY_SLASH", "weight": 40, "cooldown_frames": 30},
            {"skill": "GROUND_SLAM", "weight": 60, "cooldown_frames": 60}
        ]
    }
}