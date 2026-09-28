# entities/boss.py
# Phase 09: Boss Entity FSM & Super Armor System
# Supports multi-phase pattern shifts, super armor stun resistance, and telegraph state management.

from entities.enemy import Enemy
from data.boss_spec import BOSS_GENERAL_01_SPEC

class Boss(Enemy):
    # Boss FSM States (Extends Enemy FSM)
    STATE_IDLE = 0
    STATE_APPROACH = 1
    STATE_TELEGRAPH = 2    # Charging up attack (rendering warning area)
    STATE_ATTACK = 3       # Active attack frames with Super Armor
    STATE_STUN = 4         # Hit reaction
    STATE_PHASE_CHANGE = 5 # Brief invincibility frame on Phase 2 transition

    def __init__(self, spec=BOSS_GENERAL_01_SPEC, x=200, y=100):
        super().__init__('boss', x=x, y=y)
        self.spec = spec
        
        # Stats initialization
        self.max_hp = spec["max_hp"]
        self.hp = self.max_hp
        self.move_speed = spec["move_speed"]
        
        # Boss States
        self.phase = 1
        self.state = self.STATE_IDLE
        self.super_armor = False
        
        # Skill & Telegraph Timers (30 FPS sync)
        self.current_skill = None
        self.skill_timer = 0
        self.cooldown_timer = 0
        
        # Visual FX Flags
        self.aura_color = None
        self.is_flashing = False

    def update_boss_ai(self, player, world_width=512):
        """
        Main Boss Tick Loop called every frame (30 FPS).
        """
        if self.hp <= 0:
            return

        # 1. Check Phase Transition Threshold (HP <= 50%)
        if self.phase == 1 and (self.hp / self.max_hp) <= self.spec["phase_2_hp_threshold"]:
            self._trigger_phase_two()

        # Update Skill Cooldown
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        # 2. State Machine Logic
        if self.state == self.STATE_TELEGRAPH:
            self._update_telegraph_state()
        elif self.state == self.STATE_ATTACK:
            self._update_attack_state()
        elif self.state == self.STATE_PHASE_CHANGE:
            self._update_phase_change_state()
        elif self.state in (self.STATE_IDLE, self.STATE_APPROACH):
            self._update_decision_logic(player, world_width)

    def _trigger_phase_two(self):
        """Triggers Phase 2 rage mode with stat buffs and visual aura."""
        self.phase = 2
        self.state = self.STATE_PHASE_CHANGE
        self.skill_timer = 20 # 20 frames pause for rage roar
        self.move_speed *= self.spec["phase_2_speed_multiplier"]
        self.aura_color = self.spec["phase_2_aura_color"]
        self.super_armor = True # Invincible / Armor during phase shift

    def _update_decision_logic(self, player, world_width):
        """Melee alignment and skill pattern selection."""
        dx = player.x - self.x
        dy = player.y - self.y
        dist_x = abs(dx)
        dist_y = abs(dy)

        # Facing direction
        self.facing = 1 if dx > 0 else -1

        # Check if in range for heavy skills and cooldown ready
        if dist_x <= 40 and dist_y <= 12 and self.cooldown_timer == 0:
            # Pick Skill based on Phase pattern
            pattern = self.spec["patterns"]["PHASE_2" if self.phase == 2 else "PHASE_1"]
            selected = pattern[0] # Default to 1st heavy skill for prototype
            
            self.current_skill = self.spec["skills"][selected["skill"]]
            self.state = self.STATE_TELEGRAPH
            self.skill_timer = self.current_skill["startup_frames"]
            self.cooldown_timer = selected["cooldown_frames"]
            return

        # Standard Approach
        if dist_x > 30:
            self.x += self.facing * self.move_speed
            self.state = self.STATE_APPROACH
        else:
            self.state = self.STATE_IDLE

    def _update_telegraph_state(self):
        """Telegraph Warning Duration - Charging attack."""
        self.super_armor = self.current_skill.get("super_armor", False)
        self.skill_timer -= 1
        
        if self.skill_timer <= 0:
            # Transition to Active Attack
            self.state = self.STATE_ATTACK
            self.skill_timer = self.current_skill["active_frames"]

    def _update_attack_state(self):
        """Active Attack Hitbox Duration."""
        self.is_attacking = True
        self.skill_timer -= 1
        
        if self.skill_timer <= 0:
            # Attack Finish -> Recovery
            self.is_attacking = False
            self.super_armor = False
            self.state = self.STATE_IDLE

    def _update_phase_change_state(self):
        """Rage Roar Animation Delay."""
        self.skill_timer -= 1
        if self.skill_timer <= 0:
            self.super_armor = False
            self.state = self.STATE_IDLE

    def take_damage(self, damage, knockback_x=0):
        """
        Hit reaction handler with Super Armor support.
        """
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0

        # If Super Armor is active, IGNORE hitstun and knockback!
        if self.super_armor:
            self.is_flashing = True # Visual impact feedback without state interrupt
            return

        # Regular Damage Hit Reaction
        self.state = self.STATE_STUN
        self.x += knockback_x