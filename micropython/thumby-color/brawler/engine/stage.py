# engine/stage.py
# Phase 12 Stage Engine: Handles Tilemaps, Camera Scrolling, Shop & Enemy Waves

from data.stage_presets import STAGE_NODES
from entities.enemy import Enemy

class StageEngine:
    def __init__(self, screen_w=128, screen_h=128):
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        # Stage Bounds & Camera
        self.stage_width = 384  # 3 Screens wide (128 x 3)
        self.camera_x = 0
        
        # Current Active Stage Config
        self.stage_data = None
        self.stage_code = "KR"
        self.bg_color = 0x31A6
        
        # Entity Containers
        self.enemies = []
        self.projectiles = []
        
        # Shop Entity Trigger
        self.shop_trigger_x = 180
        self.shop_visited = False
        
        # Stage Completion State
        self.boss_spawned = False
        self.stage_cleared = False

    def load_stage(self, stage_dict):
        """Initializes a new stage node and clears previous entities."""
        self.stage_data = stage_dict
        self.stage_code = stage_dict["id"]
        self.bg_color = stage_dict["bg_color"]
        
        self.camera_x = 0
        self.enemies.clear()
        self.projectiles.clear()
        
        self.shop_visited = False
        self.boss_spawned = False
        self.stage_cleared = False
        
        # Spawn initial Wave 1 enemies based on stage culture
        self._spawn_wave_1()

    def _spawn_wave_1(self):
        """Spawns 1st Wave: Combo Brawler & Distance Thrower."""
        self.enemies.append(Enemy(self.stage_code, "BRAWLER", 140, 90))
        self.enemies.append(Enemy(self.stage_code, "THROWER", 190, 85))

    def _spawn_wave_2(self):
        """Spawns 2nd Wave: Heavy Charger/Tanker."""
        self.enemies.append(Enemy(self.stage_code, "HEAVY", 260, 95))
        self.enemies.append(Enemy(self.stage_code, "BRAWLER", 290, 88))

    def _spawn_boss_wave(self):
        """Spawns Stage Boss at the end of the stage."""
        self.boss_spawned = True
        self.enemies.append(Enemy(self.stage_code, "BOSS", 340, 80))

    def update(self, player):
        """Updates camera scroll, enemy waves, and stage progression."""
        # 1. Smooth Camera Scroll following Player (Clamped to Stage Bounds)
        target_cam_x = player.x - (self.screen_w // 2)
        self.camera_x = max(0, min(target_cam_x, self.stage_width - self.screen_w))

        # 2. Wave 2 Trigger when player advances past 200px
        if player.x > 200 and not self.boss_spawned and len(self.enemies) == 0:
            self._spawn_wave_2()

        # 3. Boss Trigger when player reaches final stage area (> 300px)
        if player.x > 300 and not self.boss_spawned and len(self.enemies) == 0:
            self._spawn_boss_wave()

        # 4. Update Active Enemies and Collect Pending Projectiles
        active_enemies = []
        for enemy in self.enemies:
            if enemy.is_active:
                enemy.update(player.x, player.y)
                
                # Check for new enemy projectiles
                if enemy.pending_projectile:
                    self.projectiles.append(enemy.pending_projectile)
                    enemy.pending_projectile = None
                    
                active_enemies.append(enemy)

        self.enemies = active_enemies

        # 5. Check Stage Clear Condition
        if self.boss_spawned and len(self.enemies) == 0:
            self.stage_cleared = True

        # 6. Update Projectiles Movement & Bounds Cleanup
        updated_projectiles = []
        for proj in self.projectiles:
            proj["x"] += proj["vx"]
            # Keep active if within screen bounds
            if 0 <= proj["x"] - self.camera_x <= self.screen_w:
                updated_projectiles.append(proj)
        self.projectiles = updated_projectiles

    def draw(self, display):
        """Renders stage parallax background, shop marker, and entities."""
        # Render Background Color
        if hasattr(display, 'fill_rect'):
            display.fill_rect(0, 0, self.screen_w, self.screen_h, self.bg_color)
            
            # Draw Horizon Line / Ground
            display.fill_rect(0, 70, self.screen_w, 58, 0x1082)
            display.line(0, 70, self.screen_w, 70, 0xFFFF)

            # Draw Shop Structure Marker if in viewport
            shop_screen_x = int(self.shop_trigger_x - self.camera_x)
            if -20 <= shop_screen_x <= 128:
                display.rect(shop_screen_x, 40, 24, 30, 0xFFE0)
                if hasattr(display, 'text'):
                    display.text("SHOP", shop_screen_x + 2, 50, 0xFFE0)

        # Draw Projectiles
        for proj in self.projectiles:
            px = int(proj["x"] - self.camera_x)
            py = int(proj["y"])
            if 0 <= px <= 128 and hasattr(display, 'fill_rect'):
                display.fill_rect(px, py, 4, 4, 0xFFE0)

        # Draw Active Enemies
        for enemy in self.enemies:
            enemy.draw(display, self.camera_x)