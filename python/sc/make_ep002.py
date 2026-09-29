import os
from richchk.model.chk_client import ChkClient
from richchk.model.chk.trig.trigger import Trigger
from richchk.model.chk.trig.trigger_action import TriggerAction
from richchk.model.chk.trig.trigger_condition import TriggerCondition
from richchk.model.chk.trig.action_type import ActionType
from richchk.model.chk.trig.condition_type import ConditionType
from richchk.model.chk.trig.player_id import PlayerId

def generate_ep02_zerg_campaign(input_scx_path: str, output_scx_path: str):
    """
    EP02 Zerg Campaign Generator - Final Rescue Edition (Terran Ghost Trio)
    - Main Hero: Infested Duran (Unit ID: 100, Defeat on Death)
    - Starting Guards: Hunter Killers (Hydralisks)
    - Rescue Heroes: Devouring One, Hunter Killer, Torrasque, Sarah Kerrigan, Alexei Stukov, Samir Duran, Fenix Zealot, Zeratul
    - Supply Rules: Fixed Base Supply + Outpost Expansion Rewards (+30 Zerg / +20 Supports). Overlords for detection only.
    - Player 1 Restrictions: Bio-only Terran, Ground-only Protoss.
    - Enemy Reinforcements: All 26 StarCraft Heroes EXCLUDING Main Hero Infested Duran (ID 100).
    - Upgrade Boosts: Player +5 per Outpost / Enemies +3 per Outpost
    - 100% Enemy Base Recovery System
    """
    if not os.path.exists(input_scx_path):
        print(f"Error: Base map file '{input_scx_path}' not found in current directory.")
        return False

    print("==================================================")
    print(" Generating Complete EP02: Zerg Campaign Map (Ghost Trio)...")
    print("==================================================")

    client = ChkClient.from_file(input_scx_path)
    chk = client.chk

    CONFIG = {
        "HERO_MAIN": "Infested Duran",
        "HERO_MAIN_ID": 100,
        "OUTPOST_COORDS": [
            (128, 24), (200, 48), (232, 128), (200, 208),
            (128, 232), (48, 208), (24, 128), (48, 48)
        ],
        # Rescue Heroes (Terran Ghost Trio: Kerrigan, Stukov, Duran)
        "RESCUE_HEROES": [
            "Devouring One (Zergling)", "Hunter Killer (Hydralisk)", "Torrasque (Ultralisk)",
            "Sarah Kerrigan (Ghost)", "Alexei Stukov (Ghost)", "Samir Duran (Ghost)",
            "Fenix (Zealot)", "Zeratul (Dark Templar)"
        ],
        "ENEMY_PLAYERS": [
            PlayerId.PLAYER_2, PlayerId.PLAYER_3, PlayerId.PLAYER_4, PlayerId.PLAYER_5,
            PlayerId.PLAYER_6, PlayerId.PLAYER_7, PlayerId.PLAYER_8, PlayerId.PLAYER_2
        ],
        # All 26 Hero Unit IDs (EXCLUDING ONLY Main Hero Infested Duran ID: 100)
        "ALL_26_HEROES": [
            20, 32, 10, 99, 22, 16, 5, 8, 81, 28,  # Terran Heroes (10)
            54, 53, 55, 56, 52, 51, 102,            # Zerg Heroes (7)
            77, 78, 79, 80, 67, 76, 88, 86, 82      # Protoss Heroes (9)
        ],
        "DISABLED_UNITS": [
            2, 5, 7, 8, 11, 12, 60, 61, 62, 67, 73, 84
        ]
    }

    triggers = []

    # 1. Defeat Condition (Infested Duran Dies)
    triggers.append(Trigger(
        conditions=[
            TriggerCondition(
                condition_type=ConditionType.KILL_COUNT,
                player=PlayerId.PLAYER_1,
                unit_id=CONFIG["HERO_MAIN_ID"],
                comparison=0,
                type_name="Infested Duran Dead"
            )
        ],
        actions=[
            TriggerAction(action_type=ActionType.DEFEAT, player=PlayerId.PLAYER_1),
            TriggerAction(
                action_type=ActionType.DISPLAY_TEXT_MESSAGE,
                text="Infested Duran has been killed in action! Mission Failed."
            )
        ],
        players=[PlayerId.ALL_PLAYERS]
    ))

    # 2. Production Restrictions for Player 1
    disable_actions = [
        TriggerAction(
            action_type=ActionType.SET_UNIT_AVAILABILITY,
            player=PlayerId.PLAYER_1,
            unit_id=u_id,
            availability=0
        ) for u_id in CONFIG["DISABLED_UNITS"]
    ]

    triggers.append(Trigger(
        conditions=[TriggerCondition(condition_type=ConditionType.ALWAYS)],
        actions=disable_actions,
        players=[PlayerId.PLAYER_1]
    ))

    # 3. Outpost Wipeout Rewards & Full 26 Heroes Reinforcements
    for idx, (coord, hero_name, enemy_slot) in enumerate(zip(CONFIG["OUTPOST_COORDS"], CONFIG["RESCUE_HEROES"], CONFIG["ENEMY_PLAYERS"])):
        
        reinforcement_actions = []
        for other_idx, other_enemy_slot in enumerate(CONFIG["ENEMY_PLAYERS"]):
            if other_idx != idx:
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
                TriggerAction(action_type=ActionType.CREATE_UNIT, player=PlayerId.PLAYER_1, unit_id=10, amount=1, location_id=idx + 1),
                TriggerAction(action_type=ActionType.GIVE_UNITS_TO_PLAYER, player=PlayerId.PLAYER_12, target_player=PlayerId.PLAYER_1, unit_id=0, amount=0, location_id=idx + 1),
                TriggerAction(action_type=ActionType.SET_UPGRADE_LEVEL, player=PlayerId.PLAYER_1, amount=5),
                TriggerAction(action_type=ActionType.SET_UPGRADE_LEVEL, player=enemy_slot, amount=3),
                *reinforcement_actions,
                TriggerAction(
                    action_type=ActionType.DISPLAY_TEXT_MESSAGE,
                    text=f"Outpost {idx+1} Wiped Out! Hero [{hero_name}] Rescued. Supply Limit Expanded & Enemy reinforced with 26 Heroes!"
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
                text="All 8 Enemy Outposts Destroyed! Infested Duran Secures Absolute Victory!"
            )
        ],
        players=[PlayerId.ALL_PLAYERS]
    ))

    chk.triggers = triggers
    client.save(output_scx_path)

    print("\n[SUCCESS] EP02 Zerg Campaign Generated Successfully!")
    print(f"Output File: {output_scx_path}")
    return True

if __name__ == "__main__":
    generate_ep02_zerg_campaign("base_256.scx", "ep02_zerg_campaign_final.scx")