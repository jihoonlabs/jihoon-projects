# entities/enemy.py
# Phase 12 Enemy Mechanics: State Machine, 3-Hit Combos, Projectiles, and Boss AI

import random
from data.enemy_presets import ENEMY_PRESETS

class Enemy:
    # Action States
    STATE_IDLE = 0
    STATE_WALK = 1
    STATE_WINDUP = 2
    STATE_ATTACK = 3
    STATE_HIT = 4
    STATE_DEAD = 5

    def __init__(self, stage_code, enemy_role, x, y):
        self.stage_code = stage_code
        self.role = enemy_role
        
        # Load enemy spec from data presets
        self.spec = ENEMY_PRESETS.get(stage_code, {}).get(enemy_role, ENEMY_PRESETS["KR"]["BRAWLER"])
        
        self.name = self.spec["name"]
        self.w = self.spec["sprite_w"]
        self.h = self.spec["sprite_h"]
        self.max_hp = self.spec["max_hp"]
        self.hp = self.max_hp
        self.speed = self.spec["speed"]
        self.color = self.spec["color"]
        self.attack_type = self.spec["attack_type"]
        self.attack_range = self.spec["attack_range"]

        # World Position & Physics
        self.x = float(x)
        self.y = float(y)
        self.facing_right = False
        
        # FSM State & Timers
        self.state = self.STATE_IDLE
        self.state_timer = 0
        self.is_active = True
        
        # Combo Tracker for Brawler Types
        self.combo_step = 0
        self.combo_timer = 0
        
        # Projectile Trigger Flag
        self.pending_projectile = None

    def update(self, player_x, player_y):
        """Main AI loop driven by player position and state machine."""
        if not self.is_active or self.state == self.STATE_DEAD:
            return

        self.state_timer += 1
        
        # Face player direction
        if self.x < player_x:
            self.facing_right = True
        else:
            self.facing_right = False

        # Calculate Manhattan/Euclidean distance to player
        dx = player_x - self.x
        dy = player_y - self.y
        dist_x = abs(dx)
        dist_y = abs(dy)

        # State Machine Execution
        if self.state == self.STATE_IDLE:
            if self.state_timer > 10:
                self.state = self.STATE_WALK
                self.state_timer = 0

        elif self.state == self.STATE_WALK:
            # Move towards player if outside attack range
            if dist_x > self.attack_range or dist_y > 4:
                move_x = (1.0 if dx > 0 else -1.0) * self.speed
                move_y = (0.5 if dy > 0 else -0.5) * self.speed
                self.x += move_x
                self.y += move_y
            else:
                # Within range, trigger attack windup
                self.state = self.STATE_WINDUP
                self.state_timer = 0

        elif self.state == self.STATE_WINDUP:
            # Telegraphing attack to player
            if self.state_timer >= 12:
                self.state = self.STATE_ATTACK
                self.state_timer = 0
                self.combo_step = 0

        elif self.state == self.STATE_ATTACK:
            self._process_attack_logic(player_x, player_y, dist_x, dist_y)

        elif self.state == self.STATE_HIT:
            if self.state_timer >= 10:
                self.state = self.STATE_IDLE
                self.state_timer = 0

    def _process_attack_logic(self, player_x, player_y, dist_x, dist_y):
        """Processes combo hits, projectile spawning, and heavy attacks."""
        if self.attack_type == "COMBO_3HIT":
            combo_spec = self.spec.get("combo_spec", [])
            if self.combo_step < len(combo_spec):
                self.combo_timer += 1
                current_hit_data = combo_spec[self.combo_step]
                
                # Advance through 1-2-3 combo steps
                if self.combo_timer >= current_hit_data["windup"] * 3:
                    self.combo_step += 1
                    self.combo_timer = 0
            else:
                # Reset combo attack cycle
                self.state = self.STATE_IDLE
                self.state_timer = 0

        elif self.attack_type == "PROJECTILE":
            # Spawn projectile on first frame of attack
            if self.state_timer == 1:
                proj_x = self.x + (self.w if self.facing_right else -8)
                proj_y = self.y + 6
                dir_x = 1 if self.facing_right else -1
                self.pending_projectile = {
                    "kind": self.spec.get("projectile_type", "STONE"),
                    "x": proj_x,
                    "y": proj_y,
                    "vx": dir_x * 3.5,
                    "damage": self.spec["damage"]
                }
            if self.state_timer >= 15:
                self.state = self.STATE_IDLE
                self.state_timer = 0

        else:  # CHARGE_TACKLE / HEAVY_SLASH / BOSS_PATTERN
            if self.state_timer >= 20:
                self.state = self.STATE_IDLE
                self.state_timer = 0

    def take_damage(self, amount, knockback=False):
        """Handles damage intake and hit reaction state."""
        if self.state == self.STATE_DEAD:
            return

        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.state = self.STATE_DEAD
            self.is_active = False
        else:
            self.state = self.STATE_HIT
            self.state_timer = 0
            if knockback:
                self.x += (-6 if self.facing_right else 6)

    def draw(self, display, camera_x=0):
        """Renders enemy sprite, health bar, and attack animations."""
        if not self.is_active:
            return

        screen_x = int(self.x - camera_x)
        screen_y = int(self.y)

        # Simple render guard for 128x128 bounds
        if screen_x + self.w < 0 or screen_x > 128:
            return

        # Flash color on hit state
        draw_color = 0xFFFF if self.state == self.STATE_HIT else self.color

        if hasattr(display, 'fill_rect'):
            # Render Body
            display.fill_rect(screen_x, screen_y, self.w, self.h, draw_color)
            
            # Telegraph/Windup Indicator (Red Box)
            if self.state == self.STATE_WINDUP:
                display.rect(screen_x - 1, screen_y - 1, self.w + 2, self.h + 2, 0xF800)
            
            # Combo Hit Visual Offset
            if self.state == self.STATE_ATTACK and self.attack_type == "COMBO_3HIT":
                fist_x = screen_x + (self.w if self.facing_right else -4)
                display.fill_rect(fist_x, screen_y + 8, 4, 4, 0xFFE0)

            # Health Bar above Head
            if self.hp < self.max_hp and self.state != self.STATE_DEAD:
                hp_pct = max(0, self.hp / self.max_hp)
                bar_w = int(self.w * hp_pct)
                display.fill_rect(screen_x, screen_y - 4, self.w, 2, 0x0000)
                display.fill_rect(screen_x, screen_y - 4, bar_w, 2, 0x07E0)