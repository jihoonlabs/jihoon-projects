import random

class DropSystem:
    @staticmethod
    def calculate_drop(enemy_drop_table, player_luck):
        # Base drop rate boosted by LUCK stat
        luck_modifier = 1.0 + (player_luck * 0.05)
        roll = random.random()

        for item_id, base_rate, item_type in enemy_drop_table:
            adjusted_rate = base_rate * luck_modifier
            if roll <= adjusted_rate:
                return {"id": item_id, "type": item_type} # WEAPON, ARMOR, ACCESSORY
        return None