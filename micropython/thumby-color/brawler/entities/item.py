# entities/item.py
# Phase 10: Field Item & Pickup Pipeline
# Manages collectible coins, health consumables, and throwable weapons with 3D volume overlap.

class Item:
    # Item Types
    TYPE_COIN = "COIN"
    TYPE_HEALTH = "HEALTH"
    TYPE_WEAPON = "WEAPON"

    def __init__(self, item_type, x, y, z=0, value=10, name="Item"):
        self.type = item_type
        self.x = x
        self.y = y
        self.z = z # Parabola arc drop height
        self.value = value
        self.name = name
        
        # 3D Volume Overlap Hitbox Sizes (Compact pickup volume)
        self.size_x = 10
        self.size_y = 6
        self.size_z = 12
        
        # Item Bounce/Drop Animation state (When dropped from props/enemies)
        self.vz = 2.5 # Initial pop-up velocity on drop
        self.is_grounded = False
        self.is_collected = False
        
        # Visual Blink on Despawn Warning
        self.lifetime_frames = 300 # Despawns after 10 seconds at 30 FPS
        self.visible = True

    def update(self):
        """
        Main tick method called every frame (30 FPS).
        Handles gravity bounce logic and despawn timer.
        """
        if self.is_collected:
            return

        # 1. Physics: Drop Bounce & Arc Trajectory
        if not self.is_grounded:
            self.z += self.vz
            self.vz -= 0.35 # Gravity acceleration
            
            if self.z <= 0:
                self.z = 0
                self.vz = -self.vz * 0.4 # Bounce coefficient
                if abs(self.vz) < 0.5:
                    self.vz = 0
                    self.is_grounded = True

        # 2. Despawn Timer
        self.lifetime_frames -= 1
        if self.lifetime_frames <= 0:
            self.is_collected = True # Mark for cleanup

        # Blinking animation before despawning (Last 2 seconds)
        if self.lifetime_frames < 60:
            self.visible = (self.lifetime_frames // 4) % 2 == 0

    def check_pickup(self, player):
        """
        Checks 3D Volume overlap with Player box.
        """
        if self.is_collected or not self.visible:
            return False

        # Spatial X, Y, Z Overlap Checks
        dx = abs(self.x - player.x)
        dy = abs(self.y - player.y)
        dz = abs(self.z - getattr(player, 'z', 0))

        if dx <= (self.size_x + 8) and dy <= (self.size_y + 4) and dz <= (self.size_z + 8):
            self.on_collect(player)
            self.is_collected = True
            return True

        return False

    def on_collect(self, player):
        """
        Applies item effects directly to player stats.
        """
        if self.type == self.TYPE_COIN:
            player.coins = getattr(player, 'coins', 0) + self.value
            
        elif self.type == self.TYPE_HEALTH:
            player.hp = min(getattr(player, 'max_hp', 100), getattr(player, 'hp', 0) + self.value)
            
        elif self.type == self.TYPE_WEAPON:
            if hasattr(player, 'equip_weapon'):
                player.equip_weapon(self.name, durability=self.value)

    def draw(self, display, camera):
        """
        Renders item sprite/primitive on Thumby Color display.
        """
        if self.is_collected or not self.visible:
            return

        screen_x = int(self.x - camera.x)
        screen_y = int(self.y - self.z) # Y-sorting ground position minus Z-height

        # Color mapping (RGB565)
        color = 0xFFE0 # Gold for Coin
        if self.type == self.TYPE_HEALTH:
            color = 0x07E0 # Green for Health
        elif self.type == self.TYPE_WEAPON:
            color = 0x001F # Blue for Weapon

        if hasattr(display, 'fill_rect'):
            display.fill_rect(screen_x - 3, screen_y - 3, 6, 6, color)