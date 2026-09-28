# data/shop_data.py
# Phase 12 Shop Catalog Spec (Common Tools + Area Specialties)

SHOP_CATALOGS = {
    # 1지역: 주막거리 상점
    1: {
        "shop_name": "Jumak Street Shop",
        "common": [
            {"id": "WHETSTONE", "name": "Whetstone", "price": 20, "type": "REPAIR", "repair_val": 50},
            {"id": "GUKBAP",    "name": "Hot Gukbap", "price": 15, "type": "HEAL",   "heal_val": 30}
        ],
        "specialties": [
            {"id": "WOODEN_SWORD", "name": "Wooden Sword", "price": 40, "type": "WEAPON", "kind": "BLADE", "durability": 40, "reach": 24},
            {"id": "SKILL_CHULSAN", "name": "Scroll: Chulsan", "price": 80, "type": "SKILL",  "skill_id": "CHULSAN_GO"}
        ]
    },
    # 2지역: 산채 암시장 상점
    2: {
        "shop_name": "Mountain Market",
        "common": [
            {"id": "WHETSTONE", "name": "Whetstone", "price": 20, "type": "REPAIR", "repair_val": 50},
            {"id": "GUKBAP",    "name": "Hot Gukbap", "price": 15, "type": "HEAL",   "heal_val": 30}
        ],
        "specialties": [
            {"id": "MATCHLOCK",    "name": "Matchlock Gun", "price": 70, "type": "WEAPON", "kind": "GUN",   "durability": 20, "reach": 80},
            {"id": "SKILL_SEUNGRYONG", "name": "Scroll: Seungryong", "price": 120, "type": "SKILL", "skill_id": "SEUNGRYONG_KICK"}
        ]
    }
}