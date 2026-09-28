# data/stage_presets.py
# Home-Origin Starting Route & Overseas Expedition Manager

STAGE_NODES = {
    "KR": {
        "id": "KR",
        "title": "Joseon Jumak Street",
        "bg_color": 0x31A6,
        "shop_id": 1,
        "boss_id": "BOSS_GATEKEEPER"
    },
    "CN": {
        "id": "CN",
        "title": "Bamboo Forest Temple",
        "bg_color": 0x0320,
        "shop_id": 2,
        "boss_id": "BOSS_WUSHU_MASTER"
    },
    "JP": {
        "id": "JP",
        "title": "Ronin Castle Night",
        "bg_color": 0x1084,
        "shop_id": 3,
        "boss_id": "BOSS_SHOGUN_GUARD"
    }
}

class HomeOriginRouteManager:
    def __init__(self, player_culture="KR"):
        self.player_culture = player_culture
        # Stage 1 is always the player's home ground
        self.visited = [player_culture]
        self.current_stage = player_culture

    def get_initial_stage(self):
        """Returns the home-ground stage for Stage 1."""
        return STAGE_NODES[self.player_culture]

    def get_expedition_choices(self):
        """Returns remaining overseas stages for player branching choice."""
        all_ids = ["KR", "CN", "JP"]
        remaining = [s_id for s_id in all_ids if s_id not in self.visited]
        return [STAGE_NODES[s_id] for s_id in remaining]

    def select_next_stage(self, chosen_stage_id):
        """Advances to chosen overseas stage."""
        self.visited.append(chosen_stage_id)
        self.current_stage = chosen_stage_id
        return STAGE_NODES[chosen_stage_id]