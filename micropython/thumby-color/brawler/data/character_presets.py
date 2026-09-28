# data/character_presets.py
# Phase 12 Refactored Asset Specs: Character Customization Presets

# All characters share exact identical combat stats for optimal balance!
COMMON_HERO_STATS = {
    "sprite_w": 16,
    "sprite_h": 20,
    "max_hp": 100,
    "base_atk": 10,
    "walk_speed": 2.0,
    "hand_anchor": {
        "right": {"x": 5, "y": -5},
        "left":  {"x": -5, "y": -5}
    }
}

GENDER_OPTIONS = [
    {"id": "MALE", "label": "Male"},
    {"id": "FEMALE", "label": "Female"}
]

OUTFIT_OPTIONS = [
    {
        "id": "KR",
        "name": "Joseon (KR)",
        "hat_m": "Gat (Tophat)",
        "hat_f": "Daeng'gi",
        "desc": "Joseon Musa Outfit"
    },
    {
        "id": "CN",
        "name": "Wushu (CN)",
        "hat_m": "Headband",
        "hat_f": "Hairpin",
        "desc": "Wushu Robe Outfit"
    },
    {
        "id": "JP",
        "name": "Ronin (JP)",
        "hat_m": "Sasa Hat",
        "hat_f": "Kunoichi Band",
        "desc": "Ronin Hakama Outfit"
    }
]

# 7 Traditional Costume Color Presets (RGB565)
PALETTE_PRESETS = [
    {"id": "WHITE",  "name": "Baek-Ui (White)",   "color": 0xFFFF},
    {"id": "BLACK",  "name": "Chil-Heuk (Black)", "color": 0x1082},
    {"id": "RED",    "name": "Ju-Hong (Red)",     "color": 0xF800},
    {"id": "BLUE",   "name": "Cheong-Ram (Blue)", "color": 0x001F},
    {"id": "GREEN",  "name": "Bi-Chwi (Green)",   "color": 0x07E0},
    {"id": "YELLOW", "name": "Hwang-Geum (Gold)",  "color": 0xFFE0},
    {"id": "PURPLE", "name": "Ja-Ja (Purple)",     "color": 0x780F}
]