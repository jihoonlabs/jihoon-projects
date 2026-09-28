# ui/shop.py
# Phase 10: Town Shop UI & Transaction System
# Compact shop menu optimized for 128x128 MicroPython display.

class ShopUI:
    def __init__(self, screen_w=128, screen_h=128):
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        self.active = False
        self.selected_index = 0
        self.message = ""
        self.message_timer = 0
        
        # Shop Catalog Items
        self.catalog = [
            {"id": "RECOVER_HP",  "name": "Heal HP (+30)",  "cost": 15, "type": "HEAL",   "val": 30},
            {"id": "REFILL_AMMO", "name": "Refill Weapon",  "cost": 20, "type": "REPAIR", "val": None},
            {"id": "UPGRADE_ATK", "name": "ATK Up (+2)",    "cost": 40, "type": "ATK",    "val": 2},
            {"id": "SKILL_SWEEP", "name": "Sweep Scroll",   "cost": 60, "type": "SKILL",  "val": "SWEEP_KICK"}
        ]

    def open_shop(self):
        """Activates the shop UI overlay."""
        self.active = True
        self.selected_index = 0
        self.message = "Welcome to Shop!"
        self.message_timer = 60

    def close_shop(self):
        """Closes the shop UI overlay."""
        self.active = False

    def handle_input(self, button_up, button_down, button_a, button_b, player):
        """
        Handles DPAD navigation and purchase transactions.
        """
        if not self.active:
            return

        # Navigate Menu
        if button_up:
            self.selected_index = (self.selected_index - 1) % len(self.catalog)
        elif button_down:
            self.selected_index = (self.selected_index + 1) % len(self.catalog)

        # Exit Shop (B button)
        if button_b:
            self.close_shop()
            return

        # Purchase Item (A button)
        if button_a:
            item = self.catalog[self.selected_index]
            player_coins = getattr(player, 'coins', 0)

            if player_coins < item["cost"]:
                self.message = "Not enough coins!"
                self.message_timer = 45
                return

            # Execute Purchase Logic
            success = self._apply_purchase(item, player)
            if success:
                player.coins -= item["cost"]
                self.message = f"Bought {item['name']}!"
                self.message_timer = 45

    def _apply_purchase(self, item, player):
        """Applies item benefits directly to player entity."""
        i_type = item["type"]
        
        if i_type == "HEAL":
            max_hp = getattr(player, 'max_hp', 100)
            if getattr(player, 'hp', 0) >= max_hp:
                self.message = "HP is already full!"
                self.message_timer = 45
                return False
            player.hp = min(max_hp, player.hp + item["val"])
            return True

        elif i_type == "REPAIR":
            current_weapon = getattr(player, 'equipped_weapon', None)
            if not current_weapon or current_weapon.id == "BARE_HANDS":
                self.message = "No weapon to refill!"
                self.message_timer = 45
                return False
            current_weapon.reload_or_repair()
            return True

        elif i_type == "ATK":
            player.base_atk = getattr(player, 'base_atk', 10) + item["val"]
            return True

        elif i_type == "SKILL":
            if hasattr(player, 'learn_skill'):
                player.learn_skill(item["val"])
            return True

        return False

    def update(self):
        """Updates shop message popup timers."""
        if self.message_timer > 0:
            self.message_timer -= 1

    def draw(self, display, player):
        """Renders 128x128 shop overlay on Thumby Color display."""
        if not self.active:
            return

        # Background overlay
        if hasattr(display, 'fill_rect'):
            display.fill_rect(8, 8, 112, 112, 0x0000)
            display.rect(8, 8, 112, 112, 0xFFFF)

        if hasattr(display, 'text'):
            # Title & Player Coins
            coins = getattr(player, 'coins', 0)
            display.text("TOWN SHOP", 14, 12, 0xFFE0) # Gold Title
            display.text(f"COIN:{coins}", 74, 12, 0xFFFF)

            # Item List (4 Items)
            start_y = 26
            for idx, item in enumerate(self.catalog):
                y = start_y + (idx * 14)
                cursor = ">" if idx == self.selected_index else " "
                color = 0xFFE0 if idx == self.selected_index else 0xFFFF
                display.text(f"{cursor}{item['name'][:10]} {item['cost']}G", 12, y, color)

            # Message / Navigation Hint Bar
            if self.message_timer > 0:
                display.text(self.message[:15], 12, 106, 0x07E0) # Green notification
            else:
                display.text("[A]Buy  [B]Exit", 14, 106, 0x8410)