# data/enemy_presets.py
# Stage-Specific Enemy & Boss Presets (4 Roles per Stage)

ENEMY_PRESETS = {
    # -------------------------------------------------------------
    # 1. KOREA (KR) - Joseon Theme
    # -------------------------------------------------------------
    "KR": {
        "BRAWLER": {
            "name": "Joseon Brawler",
            "sprite_w": 16, "sprite_h": 20, "max_hp": 30, "speed": 1.3,
            "attack_type": "COMBO_3HIT",
            "combo_spec": [
                {"hit": 1, "damage": 3, "windup": 3, "stun": 10},
                {"hit": 2, "damage": 3, "windup": 2, "stun": 10},
                {"hit": 3, "damage": 10, "windup": 4, "knockback": True}
            ],
            "attack_range": 14, "color": 0xC400
        },
        "THROWER": {
            "name": "Stone Thrower",
            "sprite_w": 16, "sprite_h": 20, "max_hp": 20, "speed": 1.5,
            "attack_type": "PROJECTILE", "projectile_type": "STONE",
            "damage": 6, "attack_range": 60, "color": 0x03E0
        },
        "HEAVY": {
            "name": "Mountain Bandit",
            "sprite_w": 18, "sprite_h": 22, "max_hp": 60, "speed": 0.9,
            "attack_type": "CHARGE_TACKLE", "damage": 12,
            "attack_range": 22, "color": 0x8A00
        },
        "BOSS": {
            "name": "Gate Guard Boss",
            "sprite_w": 20, "sprite_h": 24, "max_hp": 150, "speed": 1.0,
            "attack_type": "BOSS_PATTERN", "attack_range": 28, "color": 0x7800
        }
    },

    # -------------------------------------------------------------
    # 2. CHINA (CN) - Wushu Theme
    # -------------------------------------------------------------
    "CN": {
        "BRAWLER": {
            "name": "Wushu Monk",
            "sprite_w": 16, "sprite_h": 20, "max_hp": 35, "speed": 1.4,
            "attack_type": "COMBO_3HIT",
            "combo_spec": [
                {"hit": 1, "damage": 4, "windup": 2, "stun": 8},
                {"hit": 2, "damage": 4, "windup": 2, "stun": 8},
                {"hit": 3, "damage": 12, "windup": 3, "knockback": True}
            ],
            "attack_range": 15, "color": 0xFFE0
        },
        "THROWER": {
            "name": "Dagger Assassin",
            "sprite_w": 16, "sprite_h": 20, "max_hp": 22, "speed": 1.6,
            "attack_type": "PROJECTILE", "projectile_type": "DAGGER",
            "damage": 7, "attack_range": 65, "color": 0x07FF
        },
        "HEAVY": {
            "name": "Iron Body Guard",
            "sprite_w": 18, "sprite_h": 22, "max_hp": 70, "speed": 0.8,
            "attack_type": "GRAB_SLAM", "damage": 15,
            "attack_range": 16, "color": 0x9B20
        },
        "BOSS": {
            "name": "Wushu Grandmaster",
            "sprite_w": 20, "sprite_h": 24, "max_hp": 160, "speed": 1.2,
            "attack_type": "BOSS_PATTERN", "attack_range": 30, "color": 0xF81F
        }
    },

    # -------------------------------------------------------------
    # 3. JAPAN (JP) - Ronin Theme
    # -------------------------------------------------------------
    "JP": {
        "BRAWLER": {
            "name": "Ronin Swordsman",
            "sprite_w": 16, "sprite_h": 20, "max_hp": 40, "speed": 1.2,
            "attack_type": "COMBO_3HIT",
            "combo_spec": [
                {"hit": 1, "damage": 5, "windup": 3, "stun": 12},
                {"hit": 2, "damage": 5, "windup": 3, "stun": 12},
                {"hit": 3, "damage": 14, "windup": 5, "knockback": True}
            ],
            "attack_range": 18, "color": 0x1084
        },
        "THROWER": {
            "name": "Kunoichi",
            "sprite_w": 16, "sprite_h": 20, "max_hp": 25, "speed": 1.7,
            "attack_type": "PROJECTILE", "projectile_type": "SHURIKEN",
            "damage": 8, "attack_range": 70, "color": 0x780F
        },
        "HEAVY": {
            "name": "Armored Samurai",
            "sprite_w": 18, "sprite_h": 22, "max_hp": 80, "speed": 0.7,
            "attack_type": "HEAVY_SLASH", "damage": 18,
            "attack_range": 24, "color": 0x2100
        },
        "BOSS": {
            "name": "Shogun Guardian",
            "sprite_w": 20, "sprite_h": 24, "max_hp": 180, "speed": 1.1,
            "attack_type": "BOSS_PATTERN", "attack_range": 32, "color": 0x0000
        }
    }
}