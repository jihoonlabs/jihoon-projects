import thumby
import time
from engine.camera import Camera
from engine.debug import DebugManager
from entities.player import Player
from entities.enemy import Enemy
from gfx.renderer import Renderer

# Phase 08 & 09 Modules
from data.stage_01 import STAGE_01_DATA
from engine.stage_manager import StageManager
from ui.go_indicator import GoIndicator
from ui.dialogue import DialogueUI
from data.boss_spec import BOSS_GENERAL_01_SPEC
from entities.boss import Boss
from gfx.telegraph import TelegraphVisualizer

# Phase 10 Modules
from entities.item import Item
from engine.weapon import Weapon
from ui.shop import ShopUI
from engine.skill_manager import SkillManager

thumby.display.setFPS(30)

COLOR_WHITE = 0xFFFF
COLOR_GOLD = 0xFFE0
COLOR_RED = 0xF800

# 1. Engine & Entity Initialization
camera = Camera(world_width=STAGE_01_DATA["world_width"])
player = Player(x=40, y=80)
boss = Boss(spec=BOSS_GENERAL_01_SPEC, x=380, y=90)
renderer = Renderer()
debug_mgr = DebugManager()
telegraph_vis = TelegraphVisualizer()

# Phase 10 Subsystems
shop_ui = ShopUI(screen_w=128, screen_h=128)
skill_mgr = SkillManager()

# Default Player Stats Setup for Phase 10
player.coins = 50
player.equipped_weapon = Weapon("BARE_HANDS")
player.skill_mgr = skill_mgr

def player_learn_skill(skill_id):
    skill_mgr.learn_skill(skill_id)
player.learn_skill = player_learn_skill

# Field Entity Pools
field_items = [
    Item(Item.TYPE_COIN, x=100, y=85, value=20),
    Item(Item.TYPE_HEALTH, x=120, y=95, value=25)
]
entities = [player, boss]

def enemy_factory(e_type, spawn_x, spawn_y, direction):
    """Spawns wave enemies requested by StageManager."""
    enemy = Enemy(e_type, x=spawn_x, y=spawn_y)
    enemy.facing = direction
    entities.append(enemy)
    return enemy

stage_mgr = StageManager(STAGE_01_DATA, camera, enemy_factory=enemy_factory)
go_indicator = GoIndicator(screen_width=128, screen_height=128)
dialogue_ui = DialogueUI(screen_width=128, screen_height=128)

hitstop_frames = 0

while True:
    debug_mgr.update_telemetry()

    if thumby.buttonSelect.justPressed():
        # Toggle Debug or Open Shop Menu for Testing
        if debug_mgr.level == 0:
            shop_ui.open_shop()
        debug_mgr.toggle_level()

    # ----------------------------------------------------
    # A. UI Input Handling (Shop & Dialogue)
    # ----------------------------------------------------
    if shop_ui.active:
        shop_ui.handle_input(
            button_up=thumby.buttonUp.justPressed(),
            button_down=thumby.buttonDown.justPressed(),
            button_a=thumby.buttonA.justPressed(),
            button_b=thumby.buttonB.justPressed(),
            player=player
        )
        shop_ui.update()

    elif dialogue_ui.active:
        dialogue_ui.handle_input(thumby.buttonA.justPressed())
        dialogue_ui.update()

    # ----------------------------------------------------
    # B. Gameplay Logic (Active when UIs are closed)
    # ----------------------------------------------------
    else:
        if hitstop_frames > 0:
            hitstop_frames -= 1
        else:
            # Stage Manager & Skill Cooldown Updates
            world_enemies = [e for e in entities if (isinstance(e, Enemy) or isinstance(e, Boss))]
            stage_mgr.update(player, world_enemies)
            skill_mgr.update()

            # Trigger Dialogue Queue
            if stage_mgr.current_dialogue:
                dialogue_ui.start_dialogue(stage_mgr.current_dialogue)
                stage_mgr.current_dialogue = None

            # Player Updates & Controls
            player.update(world_width=camera.world_width, debug_mgr=debug_mgr)

            if thumby.buttonRight.pressed():
                stage_mgr.on_player_move_forward()

            # --- Phase 10 Input: Weapon Throwing (A + B) ---
            if thumby.buttonA.pressed() and thumby.buttonB.pressed():
                throw_spec = player.equipped_weapon.throw_weapon()
                if throw_spec:
                    camera.trigger_shake(2.0)
                    # Apply throw impact to nearest enemy
                    for enemy in world_enemies:
                        if getattr(enemy, 'hp', 0) > 0 and abs(enemy.x - player.x) < throw_spec["w"]:
                            enemy.take_damage(throw_spec["damage"], throw_spec["knockback_x"])

            # --- Phase 10 Input: Skill Scroll Command Check (Direction + B) ---
            elif thumby.buttonB.justPressed():
                dpad_str = "FORWARD" if (thumby.buttonRight.pressed() or thumby.buttonLeft.pressed()) \
                           else ("UP" if thumby.buttonUp.pressed() else ("DOWN" if thumby.buttonDown.pressed() else "NEUTRAL"))
                
                triggered_skill = skill_mgr.check_skill_trigger(dpad_str, True)
                if triggered_skill:
                    # Execute Skill Attack Box
                    for enemy in world_enemies:
                        if getattr(enemy, 'hp', 0) > 0 and abs(enemy.x - player.x) < triggered_skill["hitbox_w"]:
                            if isinstance(enemy, Boss):
                                enemy.take_damage(triggered_skill["damage"], 0)
                            else:
                                enemy.take_damage(triggered_skill["damage"], triggered_skill["knockback_x"])

            # Enemy & Boss Updates
            for enemy in world_enemies:
                if isinstance(enemy, Enemy) and not isinstance(enemy, Boss) and getattr(enemy, 'hp', 0) > 0:
                    enemy.update_ai(player, world_width=camera.world_width)

            if getattr(boss, 'hp', 0) > 0:
                boss.update_boss_ai(player, world_width=camera.world_width)

            # Field Item Updates & Pickups
            for item in field_items:
                item.update()
                item.check_pickup(player)

            # Standard Hitbox Overlaps
            for enemy in world_enemies:
                if getattr(enemy, 'hp', 0) <= 0:
                    continue

                if player.is_attacking and player.hitbox:
                    if player.hitbox.check_overlap(enemy):
                        # Consume weapon ammo/durability on hit
                        if hasattr(player, 'equipped_weapon'):
                            player.equipped_weapon.use(camera=camera)

                        if isinstance(enemy, Boss):
                            enemy.take_damage(10, 2 if not enemy.super_armor else 0)

                        stop_req = player.hitbox.resolve_impact(enemy, camera=camera)
                        hitstop_frames = max(hitstop_frames, stop_req)

    # ----------------------------------------------------
    # C. Camera & Render Pipeline
    # ----------------------------------------------------
    camera.update(player.x)
    go_indicator.update(stage_mgr.show_go_indicator)

    # Render World Scene
    renderer.render_scene(camera, entities, debug_mgr=debug_mgr)

    # Render Field Items
    for item in field_items:
        item.draw(thumby.display, camera)

    # Render Boss Telegraph Warning
    if not dialogue_ui.active and not shop_ui.active and boss.hp > 0:
        telegraph_vis.draw_boss_telegraph(thumby.display, camera, boss)

    # Render UI Overlays
    if stage_mgr.show_go_indicator and not shop_ui.active:
        go_indicator.draw(thumby.display, is_active=True)

    if dialogue_ui.active:
        dialogue_ui.draw(thumby.display)

    if shop_ui.active:
        shop_ui.draw(thumby.display, player)

    # Telemetry HUD
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)

    if debug_mgr.level >= 1 and not shop_ui.active:
        weap_str = f"{player.equipped_weapon.name[:5]}:{player.equipped_weapon.ammo}"
        thumby.display.drawText(f"P10-ITEMS {debug_mgr.fps:.0f}FPS {debug_mgr.free_mem_kb}KB", 2, 2, COLOR_GOLD)
        thumby.display.drawText(f"COIN:{player.coins} WEAP:{weap_str}", 2, 8, COLOR_WHITE)

    thumby.display.update()