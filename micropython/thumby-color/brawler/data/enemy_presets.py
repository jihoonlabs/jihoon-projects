# data/enemy_presets.py
# Stage 1 Enemy & Boss Presets with Combo Mechanics

STAGE_1_ENEMIES = {
    # 1. Basic Barehand Brawler (High combo damage on full hit)
    "BAREHAND_BRAWLER": {
        "name": "Jumak Brawler",
        "sprite_w": 16,
        "sprite_h": 20,
        "max_hp": 30,
        "speed": 1.3,
        "attack_type": "COMBO_3HIT",
        "combo_spec": [
            {"hit": 1, "damage": 3, "windup": 3, "stun": 10},         # 1st: Jab
            {"hit": 2, "damage": 3, "windup": 2, "stun": 10},         # 2nd: Hook
            {"hit": 3, "damage": 10, "windup": 4, "knockback": True}   # 3rd: Finish Heavy Hit!
        ],
        "attack_range": 14,
        "color": 0xC400  # Dark Red/Brown
    },
    
    # 2. Projectile Enemy (Throws large visible stones/pots)
    "STONE_THROWER": {
        "name": "Stone Thrower",
        "sprite_w": 16,
        "sprite_h": 20,
        "max_hp": 20,
        "speed": 1.5,
        "attack_type": "PROJECTILE",
        "damage": 6,
        "attack_range": 60,
        "color": 0x03E0  # Dark Green
    },
    
    # 3. Stage 1 Boss: Gate Guard Boss
    "BOSS_GATEKEEPER": {
        "name": "Gate Guard Boss",
        "sprite_w": 20,
        "sprite_h": 24,
        "max_hp": 150,
        "speed": 1.0,
        "attack_type": "BOSS_PATTERN",
        "damage_slash": 15,
        "damage_tackle": 12,
        "damage_gun": 8,
        "attack_range": 28,
        "color": 0x7800  # Deep Crimson
    }
}