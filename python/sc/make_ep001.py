import os
from richchk.model.chk_client import ChkClient
from richchk.model.chk.trig.trigger import Trigger
from richchk.model.chk.trig.trigger_action import TriggerAction
from richchk.model.chk.trig.trigger_condition import TriggerCondition
from richchk.model.chk.trig.action_type import ActionType
from richchk.model.chk.trig.condition_type import ConditionType
from richchk.model.chk.trig.player_id import PlayerId

def generate_ep01_terran_campaign(input_scx_path: str, output_scx_path: str):
    """
    EP01 Terran Campaign Generator - Full Hero All-Stars Edition
    - Main Hero: Alexei Stukov (Ghost, Range 8, Defeat on Death)
    - 8 Rescue Heroes: Raynor(Marine), Kerrigan, Duran, Infested Duran, Fenix(Zealot), Tassadar, Zeratul, Hunter Killer
    - Enemy Reinforcements: ALL StarCraft Heroes EXCLUDING ONLY Main Hero Alexei Stukov (26 Heroes total).
      Spawns 1 unit of EVERY hero to surviving outposts upon every wipeout!
    - Upgrade Boosts: Player +5 per Outpost / Enemies +3 per Outpost
    - Archon / Dark Archon Merge Disabled for Player
    - 100% Enemy Base Recovery System
    """
    if not os.path.exists(input_scx_path):
        print(f"Error: Base map file '{input_scx_path}' not found in current directory.")
        return False

    print("==================================================")
    print(" Generating Complete EP01: Terran Campaign (Full 26 Heroes Army)...")
    print("==================================================")

    client = ChkClient.from_file(input_scx_path)
    chk = client.chk

    CONFIG = {
        "HERO_MAIN": "Alexei Stukov",
        "OUTPOST_COORDS": [
            (128, 24), (200, 48), (232, 128), (200, 208),
            (128, 232), (48, 208), (24, 128), (48, 48)
        ],
        "RESCUE_HEROES": [
            "Jim Raynor (Marine)", "Sarah Kerrigan (Ghost)", "Samir Duran (Ghost)", "Infested Duran",
            "Fenix (Zealot)", "Tassadar (High Templar)", "Zeratul (Dark Templar)", "Hunter Killer (Hydralisk)"
        ],
        "ENEMY_PLAYERS": [
            PlayerId.PLAYER_2, PlayerId.PLAYER_3, PlayerId.PLAYER_4, PlayerId.PLAYER_5,
            PlayerId.PLAYER_6, PlayerId.PLAYER_7, PlayerId.PLAYER_8, PlayerId.PLAYER_2
        ],
        # All 26 Hero Unit IDs (EXCLUDING ONLY Alexei Stukov ID: 22)
        "ALL_26_HEROES": [
            # Terran Heroes (9)
            20,  # Marine Raynor
            32,  # Vulture Raynor
            10,  # Kerrigan (Ghost)
            99,  # Samir Duran
            16,  # Gui Montag (Firebat)
            5,   # Edmund Duke (Siege Tank)
            8,   # Tom Kazansky (Wraith)
            81,  # Norad II (Battlecruiser)
            28,  # Hyperion (Battlecruiser)
            
            # Zerg Heroes (8)
            54,  # Devouring One (Zergling)
            53,  # Hunter Killer (Hydralisk)
            55,  # Kukulza (Mutalisk)
            56,  # Kukulza (Guardian)
            52,  # Matriarch (Queen)
            51,  # Torrasque (Ultralisk)
            102, # Infested Kerrigan
            100, # Infested Duran
            
            # Protoss Heroes (9)
            77,  # Fenix (Zealot)
            78,  # Fenix (Dragoon)
            79,  # Tassadar (High Templar)
            80,  # Zeratul (Dark Templar)
            67,  # Hero Archon
            76,  # Aldaris (High Templar)
            88,  # Mojo (Scout)
            86,  # Artanis (Scout)
            82   # Gantrithor (Carrier)
        ]
    }

    triggers = []

    # 1. Defeat Condition (Alexei Stukov Dies)
    triggers.append(Trigger(
        conditions=[
            TriggerCondition(
                condition_type=ConditionType.KILL_COUNT,
                player=PlayerId.PLAYER_1,
                unit_id=22,  # Alexei Stukov
                comparison=0,
                type_name="Alexei Stukov Dead"
            )
        ],
        actions=[
            TriggerAction(action_type=ActionType.DEFEAT, player=PlayerId.PLAYER_1),
            TriggerAction(
                action_type=ActionType.DISPLAY_TEXT_MESSAGE,
                text="Commander Alexei Stukov has been killed in action! Mission Failed."
            )
        ],
        players=[PlayerId.ALL_PLAYERS]
    ))

    # 2. Disable Archon / Dark Archon Merge for Player
    triggers.append(Trigger(
        conditions=[TriggerCondition(condition_type=ConditionType.ALWAYS)],
        actions=[
            TriggerAction(action_type=ActionType.SET_UNIT_AVAILABILITY, player=PlayerId.PLAYER_1, unit_id=67, availability=0),
            TriggerAction(action_type=ActionType.SET_UNIT_AVAILABILITY, player=PlayerId.PLAYER_1, unit_id=73, availability=0)
        ],
        players=[PlayerId.PLAYER_1]
    ))

    # 3. Outpost Wipeout Rewards & Full 26 Heroes Reinforcements (1 unit each)
    for idx, (coord, hero_name, enemy_slot) in enumerate(zip(CONFIG["OUTPOST_COORDS"], CONFIG["RESCUE_HEROES"], CONFIG["ENEMY_PLAYERS"])):
        
        reinforcement_actions = []
        for other_idx, other_enemy_slot in enumerate(CONFIG["ENEMY_PLAYERS"]):
            if other_idx != idx:
                # Spawn 1 unit of ALL 26 HEROES at surviving outposts
                for h_id in CONFIG["ALL_26_HEROES"]:
                    reinforcement_actions.append(
                        TriggerAction(
                            action_type=ActionType.CREATE_UNIT,
                            player=other_enemy_slot,
                            unit_id=h_id,
                            amount=1,
                            location_id=other_idx + 1
                        )
                    )

        triggers.append(Trigger(
            conditions=[
                TriggerCondition(
                    condition_type=ConditionType.COMMAND,
                    player=enemy_slot,
                    unit_id=122,
                    comparison=0,
                    type_name=f"Stasis Cell {idx+1} Destroyed"
                )
            ],
            actions=[
                # Spawn Rescued Hero for Player 1
                TriggerAction(action_type=ActionType.CREATE_UNIT, player=PlayerId.PLAYER_1, unit_id=10, amount=1, location_id=idx + 1),
                # Capture Support Base
                TriggerAction(action_type=ActionType.GIVE_UNITS_TO_PLAYER, player=PlayerId.PLAYER_12, target_player=PlayerId.PLAYER_1, unit_id=0, amount=0, location_id=idx + 1),
                # Upgrades (+5 Player / +3 Enemy)
                TriggerAction(action_type=ActionType.SET_UPGRADE_LEVEL, player=PlayerId.PLAYER_1, amount=5),
                TriggerAction(action_type=ActionType.SET_UPGRADE_LEVEL, player=enemy_slot, amount=3),
                # Spawn All 26 Heroes (1 unit each)
                *reinforcement_actions,
                TriggerAction(
                    action_type=ActionType.DISPLAY_TEXT_MESSAGE,
                    text=f"Outpost {idx+1} Wiped Out! Hero [{hero_name}] Rescued. Enemy reinforced with 26 Hero All-Stars!"
                )
            ],
            players=[PlayerId.ALL_PLAYERS]
        ))

    # 4. Enemy Outpost 100% Full Recovery Mechanism
    for idx, enemy_slot in enumerate(CONFIG["ENEMY_PLAYERS"]):
        triggers.append(Trigger(
            conditions=[
                TriggerCondition(condition_type=ConditionType.COMMAND, player=enemy_slot, unit_id=200, comparison=1, type_name=f"Enemy Outpost {idx+1} Alive")
            ],
            actions=[
                TriggerAction(action_type=ActionType.MODIFY_UNIT_HIT_POINTS, player=enemy_slot, unit_id=0, amount=100, location_id=idx + 1)
            ],
            players=[enemy_slot]
        ))

    # 5. Victory Condition
    triggers.append(Trigger(
        conditions=[
            TriggerCondition(condition_type=ConditionType.COMMAND, player=PlayerId.ALL_PLAYERS, unit_id=122, comparison=0, type_name="All Stasis Cells Destroyed")
        ],
        actions=[
            TriggerAction(action_type=ActionType.VICTORY, player=PlayerId.PLAYER_1),
            TriggerAction(
                action_type=ActionType.DISPLAY_TEXT_MESSAGE,
                text="All 8 Enemy Outposts Destroyed! Commander Alexei Stukov Secures Absolute Victory!"
            )
        ],
        players=[PlayerId.ALL_PLAYERS]
    ))

    chk.triggers = triggers
    client.save(output_scx_path)

    print("\n[SUCCESS] EP01 Terran Campaign (Full 26 Heroes) Generated Successfully!")
    print(f"Output File: {output_scx_path}")
    return True

if __name__ == "__main__":
    generate_ep01_terran_campaign("base_256.scx", "ep01_terran_campaign_final.scx")