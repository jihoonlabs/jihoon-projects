# engine/weapon.py
# Phase 10: Ground-based Martial Arts & Weapon Throw Engine
# Supports punching, shooting, and A+B weapon throwing.

class Weapon:
    KIND_UNARMED = "UNARMED"  # Bare-hands, Knuckles
    KIND_BLADE   = "BLADE"    # Sword
    KIND_GUN     = "GUN"      # Auto-Pistol, Handgun, Musket

    PRESETS = {
        "BARE_HANDS": {
            "name": "Bare Hands",
            "kind": KIND_UNARMED,
            "max_ammo": 999,
            "damage": 10,
            "hitbox_w": 16, "hitbox_h": 12,
            "cooldown": 10,
            "can_throw": False
        },
        "KNUCKLE": {
            "name": "Knuckles",
            "kind": KIND_UNARMED,
            "max_ammo": 30,
            "damage": 14,
            "hitbox_w": 12, "hitbox_h": 10,
            "cooldown": 6,
            "can_throw": True,
            "throw_damage": 18
        },
        "SWORD": {
            "name": "Steel Sword",
            "kind": KIND_BLADE,
            "max_ammo": 20,
            "damage": 20,
            "hitbox_w": 28, "hitbox_h": 16,
            "cooldown": 12,
            "can_throw": True,
            "throw_damage": 30
        },
        "AUTO_PISTOL": {
            "name": "Auto-Pistol",
            "kind": KIND_GUN,
            "max_ammo": 24,
            "damage": 8,
            "hitbox_w": 45, "hitbox_h": 8,
            "cooldown": 4,
            "can_throw": True,
            "throw_damage": 15
        },
        "HANDGUN": {
            "name": "Handgun",
            "kind": KIND_GUN,
            "max_ammo": 12,
            "damage": 16,
            "hitbox_w": 65, "hitbox_h": 8,
            "cooldown": 8,
            "can_throw": True,
            "throw_damage": 22
        },
        "MUSKET": {
            "name": "Musket Rifle",
            "kind": KIND_GUN,
            "max_ammo": 6,
            "damage": 32,
            "hitbox_w": 110, "hitbox_h": 10,
            "cooldown": 18,
            "piercing": True,
            "can_throw": True,
            "throw_damage": 35
        }
    }

    def __init__(self, weapon_id="BARE_HANDS"):
        self.id = weapon_id
        self.preset = self.PRESETS.get(weapon_id, self.PRESETS["BARE_HANDS"])
        self.kind = self.preset["kind"]
        self.name = self.preset["name"]
        
        self.max_ammo = self.preset["max_ammo"]
        self.ammo = self.max_ammo

    def use(self):
        """Standard attack/shot logic."""
        if self.id == "BARE_HANDS":
            return self.preset["cooldown"]

        if self.ammo <= 0:
            return 12  # Penalty delay when dry

        self.ammo -= 1
        return self.preset["cooldown"]

    def throw_weapon(self):
        """
        Triggered on A+B simultaneous press.
        Throws current weapon forward for heavy penetration damage and clears weapon.
        """
        if not self.preset.get("can_throw", False) or self.id == "BARE_HANDS":
            return None

        throw_spec = {
            "damage": self.preset.get("throw_damage", 20),
            "w": 80,  # Fast linear throw line
            "h": 12,
            "piercing": True,
            "knockback_x": 12
        }

        # Reset back to Bare-Hands after throw
        self.__init__("BARE_HANDS")
        return throw_spec

    def reload_or_repair(self, amount=None):
        """Replenishes ammo/durability."""
        if amount is None:
            self.ammo = self.max_ammo
        else:
            self.ammo = min(self.max_ammo, self.ammo + amount)

    def get_hitbox_spec(self):
        """Returns standard attack hitbox stats."""
        if self.id != "BARE_HANDS" and self.ammo <= 0:
            return {"damage": 5, "w": 12, "h": 10, "piercing": False}

        return {
            "damage": self.preset["damage"],
            "w": self.preset["hitbox_w"],
            "h": self.preset["hitbox_h"],
            "piercing": self.preset.get("piercing", False)
        }