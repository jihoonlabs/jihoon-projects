# engine/save_manager.py
# Phase 11: Save State Manager for RP2040 MicroPython Flash Storage
# Handles JSON serialization and safe file IO for persistent player progression.

import json

SAVE_FILE_PATH = "save_data.json"

DEFAULT_SAVE_DATA = {
    "coins": 0,
    "max_hp": 100,
    "base_atk": 10,
    "unlocked_skills": [],
    "equipped_weapon": "BARE_HANDS",
    "weapon_ammo": 999,
    "stage_index": 1
}

class SaveManager:
    @staticmethod
    def save_game(player, stage_index=1):
        """
        Serializes current player state and stage index to Flash Memory.
        Should be called on Stage Clear, Town Shop exit, or Game Save triggers.
        """
        data = {
            "coins": getattr(player, 'coins', 0),
            "max_hp": getattr(player, 'max_hp', 100),
            "base_atk": getattr(player, 'base_atk', 10),
            "unlocked_skills": getattr(player.skill_mgr, 'unlocked_skills', []) if hasattr(player, 'skill_mgr') else [],
            "equipped_weapon": player.equipped_weapon.id if hasattr(player, 'equipped_weapon') and player.equipped_weapon else "BARE_HANDS",
            "weapon_ammo": player.equipped_weapon.ammo if hasattr(player, 'equipped_weapon') and player.equipped_weapon else 999,
            "stage_index": stage_index
        }

        try:
            with open(SAVE_FILE_PATH, "w") as f:
                json.dump(data, f)
            print("[SaveManager] Game saved successfully.")
            return True
        except Exception as e:
            print(f"[SaveManager] Save failed: {e}")
            return False

    @staticmethod
    def load_game(player=None):
        """
        Loads save data from Flash Memory.
        If file doesn't exist or is corrupted, loads DEFAULT_SAVE_DATA fallback.
        Returns the data dictionary.
        """
        data = DEFAULT_SAVE_DATA.copy()

        try:
            with open(SAVE_FILE_PATH, "r") as f:
                loaded = json.load(f)
                data.update(loaded)
            print("[SaveManager] Game loaded successfully.")
        except (OSError, ValueError) as e:
            print(f"[SaveManager] No valid save file found ({e}). Loading defaults.")

        # Apply directly to player entity if passed
        if player:
            SaveManager.apply_to_player(player, data)

        return data

    @staticmethod
    def apply_to_player(player, data):
        """
        Applies loaded dictionary values onto Player entity instances.
        """
        player.coins = data.get("coins", 0)
        player.max_hp = data.get("max_hp", 100)
        player.hp = player.max_hp  # Restore full HP on load
        player.base_atk = data.get("base_atk", 10)

        # Restore Unlocked Skills
        if hasattr(player, 'skill_mgr'):
            player.skill_mgr.unlocked_skills = data.get("unlocked_skills", [])[:]

        # Restore Weapon
        weap_id = data.get("equipped_weapon", "BARE_HANDS")
        ammo = data.get("weapon_ammo", 999)
        if hasattr(player, 'equip_weapon'):
            player.equip_weapon(weap_id, durability=ammo)

    @staticmethod
    def reset_save():
        """
        Deletes or overrides save data back to fresh defaults (e.g., New Game / Hard Reset).
        """
        try:
            with open(SAVE_FILE_PATH, "w") as f:
                json.dump(DEFAULT_SAVE_DATA, f)
            print("[SaveManager] Save data reset to default.")
        except Exception as e:
            print(f"[SaveManager] Reset failed: {e}")