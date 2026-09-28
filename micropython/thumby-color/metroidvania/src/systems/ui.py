class UIHUD:
    def __init__(self):
        self.hud_height = 10  # Top 10px reserved for HUD

    def render(self, display, player):
        # Draw HP Bar (Red/White pixels)
        hp_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0
        hp_width = int(30 * hp_ratio)
        display.draw_rectangle(2, 2, 32, 4)
        display.fill_rectangle(3, 3, hp_width, 2)

        # Draw Equipped Weapon & Accessory Slot Icons
        display.draw_icon(player.equipped_weapon_icon, 100, 1)
        for i in range(player.unlocked_acc_slots):
            display.draw_icon(player.acc_icons[i], 108 + (i * 6), 1)

class EquipmentMenu:
    def __init__(self):
        self.is_active = False
        self.cursor_idx = 0  # 0: Weapon, 1: Armor, 2: Acc Slot 1..3

    def toggle(self):
        self.is_active = not self.is_active

    def update(self, btn_up, btn_down, btn_confirm, player):
        if not self.is_active:
            return

        if btn_down:
            self.cursor_idx = (self.cursor_idx + 1) % 5
        elif btn_up:
            self.cursor_idx = (self.cursor_idx - 1) % 5

        if btn_confirm:
            self.equip_selected_item(player)

    def equip_selected_item(self, player):
        # Logic for swapping weapons, armors, and accessories
        pass

    def render(self, display, player):
        if not self.is_active:
            return

        # Dim background (Pause State)
        display.draw_overlay_pause()

        # Render 128x128 Grid Menu
        display.draw_text("EQUIPMENT", 36, 10)
        display.draw_text(f"WEAPON: {player.weapon_name}", 10, 30)
        display.draw_text(f"ARMOR : {player.armor_name}", 10, 45)
        display.draw_text(f"ACC 1 : {player.acc_names[0]}", 10, 60)
        display.draw_text(f"ACC 2 : {player.acc_names[1]}", 10, 72)
        display.draw_text(f"ACC 3 : {player.acc_names[2]}", 10, 84)

        # Draw Cursor
        cursor_y_positions = [30, 45, 60, 72, 84]
        display.draw_text(">", 2, cursor_y_positions[self.cursor_idx])