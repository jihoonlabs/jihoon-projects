import thumby
import time
from engine.camera import Camera
from engine.debug import DebugManager
from entities.player import Player
from entities.enemy import Enemy
from gfx.renderer import Renderer

# Phase 08 ~ 11 Modules
from data.stage_01 import STAGE_01_DATA
from engine.stage_manager import StageManager
from ui.go_indicator import GoIndicator
from ui.dialogue import DialogueUI
from data.boss_spec import BOSS_GENERAL_01_SPEC
from entities.boss import Boss
from gfx.telegraph import TelegraphVisualizer
from entities.item import Item
from engine.weapon import Weapon
from ui.shop import ShopUI
from engine.skill_manager import SkillManager
from engine.save_manager import SaveManager
from engine.progression import ProgressionEngine

# Phase 12 Modules
from engine.audio import AudioEngine
from ui.title import TitleUI

thumby.display.setFPS(30)

COLOR_WHITE = 0xFFFF
COLOR_GOLD = 0xFFE0
COLOR_RED = 0xF800

# 1. Engine & Subsystems Initialization
camera = Camera(world_width=STAGE_01_DATA["world_width"])
player = Player(x=40, y=80)
boss = Boss(spec=BOSS_GENERAL_01_SPEC, x=380, y=90)
renderer = Renderer()
debug_mgr = DebugManager()
telegraph_vis = TelegraphVisualizer()

shop_ui = ShopUI(screen_w=128, screen_h=128)
skill_mgr = SkillManager()
progression = ProgressionEngine()

# Phase 12 Audio & Title UI Setup
audio = AudioEngine()
title_ui = TitleUI(screen_w=128, screen_h=128)

screen_flash_frames = 0  # Screen flash effect timer for heavy hits/gunshots

# Player Setup & Binding
player.equipped_weapon = Weapon("BARE_HANDS")
player.skill_mgr = skill_mgr

def player_learn_skill(skill_id):
    skill_mgr.learn_skill(skill_id)
player.learn_skill = player_learn_skill

def player_equip_weapon(weapon_id, durability=None):
    player.equipped_weapon = Weapon(weapon_id, ammo=durability)
player.equip_weapon = player_equip_weapon

field_items = [
    Item(Item.TYPE_COIN, x=100, y=85, value=20),
    Item(Item.TYPE_HEALTH, x=120, y=95, value=25)
]
entities = [player, boss]

def enemy_factory(e_type, spawn_x, spawn_y, direction):
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
    audio.update()  # Non-blocking audio timer tick

    if thumby.buttonSelect.justPressed():
        if debug_mgr.level == 0 and not title_ui.active:
            shop_ui.open_shop()
        debug_mgr.toggle_level()

    # ----------------------------------------------------
    # A. Title Screen State Handling
    # ----------------------------------------------------
    if title_ui.active:
        title_action = title_ui.handle_input(
            button_up=thumby.buttonUp.justPressed(),
            button_down=thumby.buttonDown.justPressed(),
            button_a=thumby.buttonA.justPressed()
        )
        if title_action == "NEW_GAME":
            SaveManager.reset_save()
            progression.init_from_save(player)
            audio.play_sfx_coin()
        elif title_action == "CONTINUE":
            progression.init_from_save(player)
            audio.play_sfx_coin()

        title_ui.draw(thumby.display)
        thumby.display.update()
        continue

    # ----------------------------------------------------
    # B. Active Game UI Handling (Shop, Dialogue, Game Over)
    # ----------------------------------------------------
    if shop_ui.active:
        was_active = shop_ui.active
        shop_ui.handle_input(
            button_up=thumby.buttonUp.justPressed(),
            button_down=thumby.buttonDown.justPressed(),
            button_a=thumby.buttonA.justPressed(),
            button_b=thumby.buttonB.justPressed(),
            player=player
        )
        shop_ui.update()
        
        if was_active and not shop_ui.active:
            progression.on_shop_close(player)
            audio.play_sfx_coin()

    elif dialogue_ui.active:
        dialogue_ui.handle_input(thumby.buttonA.justPressed())
        dialogue_ui.update()

    elif progression.state == ProgressionEngine.STATE_GAME_OVER:
        if thumby.buttonA.justPressed():
            progression.retry_stage(player)
            player.x, player.y = 40, 80
            boss.hp = boss.max_hp
            boss.state = boss.STATE_IDLE
            audio.play_sfx_coin()

    # ----------------------------------------------------
    # C. Main Gameplay Logic
    # ----------------------------------------------------
    else:
        if hitstop_frames > 0:
            hitstop_frames -= 1
        else:
            world_enemies = [e for e in entities if (isinstance(e, Enemy) or isinstance(e, Boss))]
            stage_mgr.update(player, world_enemies)
            skill_mgr.update()
            progression.update()

            if stage_mgr.current_dialogue:
                dialogue_ui.start_dialogue(stage_mgr.current_dialogue)
                stage_mgr.current_dialogue = None

            # Player Logic & Controls
            if player.hp > 0:
                player.update(world_width=camera.world_width, debug_mgr=debug_mgr)

                if thumby.buttonRight.pressed():
                    stage_mgr.on_player_move_forward()

                # Weapon Throw (A + B)
                if thumby.buttonA.pressed() and thumby.buttonB.pressed():
                    throw_spec = player.equipped_weapon.throw_weapon()
                    if throw_spec:
                        camera.trigger_shake(3.0)
                        screen_flash_frames = 2  # Trigger Flash
                        audio.play_sfx_gunshot()
                        for enemy in world_enemies:
                            if getattr(enemy, 'hp', 0) > 0 and abs(enemy.x - player.x) < throw_spec["w"]:
                                enemy.take_damage(throw_spec["damage"], throw_spec["knockback_x"])

                # Skill Command (Direction + B)
                elif thumby.buttonB.justPressed():
                    dpad_str = "FORWARD" if (thumby.buttonRight.pressed() or thumby.buttonLeft.pressed()) \
                               else ("UP" if thumby.buttonUp.pressed() else ("DOWN" if thumby.buttonDown.pressed() else "NEUTRAL"))
                    
                    triggered_skill = skill_mgr.check_skill_trigger(dpad_str, True)
                    if triggered_skill:
                        audio.play_sfx_skill()
                        for enemy in world_enemies:
                            if getattr(enemy, 'hp', 0) > 0 and abs(enemy.x - player.x) < triggered_skill["hitbox_w"]:
                                enemy.take_damage(triggered_skill["damage"], 0 if isinstance(enemy, Boss) else triggered_skill["knockback_x"])
            else:
                if progression.state != ProgressionEngine.STATE_GAME_OVER:
                    audio.play_sfx_game_over()
                    progression.trigger_game_over()

            # Check Boss Defeat
            if boss.hp <= 0 and progression.state == ProgressionEngine.STATE_PLAYING:
                progression.trigger_stage_clear(player)
                audio.play_sfx_coin()

            # Enemies & Boss Logic
            for enemy in world_enemies:
                if isinstance(enemy, Enemy) and not isinstance(enemy, Boss) and getattr(enemy, 'hp', 0) > 0:
                    enemy.update_ai(player, world_width=camera.world_width)

            if getattr(boss, 'hp', 0) > 0:
                boss.update_boss_ai(player, world_width=camera.world_width)

            # Field Items & Pickups
            for item in field_items:
                item.update()
                if item.check_pickup(player):
                    audio.play_sfx_coin()

            # Combat Hitbox Overlaps
            for enemy in world_enemies:
                if getattr(enemy, 'hp', 0) <= 0:
                    continue

                if player.is_attacking and player.hitbox:
                    if player.hitbox.check_overlap(enemy):
                        if hasattr(player, 'equipped_weapon'):
                            weapon_kind = player.equipped_weapon.kind
                            player.equipped_weapon.use()
                            
                            # Audio & Flash Feedback by Weapon Archetype
                            if weapon_kind == Weapon.KIND_GUN:
                                audio.play_sfx_gunshot()
                                screen_flash_frames = 2
                            elif weapon_kind == Weapon.KIND_BLADE:
                                audio.play_sfx_slash()
                            else:
                                audio.play_sfx_punch()

                        if isinstance(enemy, Boss):
                            enemy.take_damage(player.base_atk, 2 if not enemy.super_armor else 0)

                        stop_req = player.hitbox.resolve_impact(enemy, camera=camera)
                        hitstop_frames = max(hitstop_frames, stop_req)

    # ----------------------------------------------------
    # D. Camera & Rendering Pipeline
    # ----------------------------------------------------
    camera.update(player.x)
    go_indicator.update(stage_mgr.show_go_indicator)

    renderer.render_scene(camera, entities, debug_mgr=debug_mgr)

    for item in field_items:
        item.draw(thumby.display, camera)

    if not dialogue_ui.active and not shop_ui.active and boss.hp > 0:
        telegraph_vis.draw_boss_telegraph(thumby.display, camera, boss)

    if stage_mgr.show_go_indicator and not shop_ui.active:
        go_indicator.draw(thumby.display, is_active=True)

    if dialogue_ui.active:
        dialogue_ui.draw(thumby.display)

    if shop_ui.active:
        shop_ui.draw(thumby.display, player)

    progression.draw_status_overlay(thumby.display)

    # Screen Flash Overlay Effect (White Invert Flash)
    if screen_flash_frames > 0:
        screen_flash_frames -= 1
        if hasattr(thumby.display, 'fill_rect'):
            thumby.display.fill_rect(0, 0, 128, 128, COLOR_WHITE)

    # Telemetry HUD
    thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)

    if debug_mgr.level >= 1 and not shop_ui.active:
        weap_str = f"{player.equipped_weapon.name[:4]}:{player.equipped_weapon.ammo}"
        thumby.display.drawText(f"FINAL-RELEASE {debug_mgr.fps:.0f}FPS {debug_mgr.free_mem_kb}KB", 2, 2, COLOR_GOLD)
        thumby.display.drawText(f"COIN:{player.coins} HP:{player.hp} {weap_str}", 2, 8, COLOR_WHITE)

    thumby.display.update()