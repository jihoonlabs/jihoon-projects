import os

def generate_triggers():
    triggers = []

    # -------------------------------------------------------------
    # 1. Exchange System (10 Kills -> 500 Minerals)
    # -------------------------------------------------------------
    triggers.append("""
Trigger("Player 1"){
Conditions:
    Kills("Player 1", "Any unit", At Least, 10);
    Bring("Player 1", "Men", "Exchange_Beacon", At Least, 1);

Actions:
    SetKills("Player 1", "Any unit", Subtract, 10);
    SetResources("Player 1", Add, 500, Ore);
    DisplayText("Exchanged 10 Kills for 500 Minerals!", 4);
    PreserveTrigger();
}
""")

    # -------------------------------------------------------------
    # 2. Base Healing Zone (HP/Energy Restore)
    # -------------------------------------------------------------
    triggers.append("""
Trigger("Player 1"){
Conditions:
    Bring("Player 1", "Men", "Heal_Beacon", At Least, 1);

Actions:
    ModifyUnitHitPoints("Player 1", "Men", All, "Heal_Beacon", 100);
    ModifyUnitEnergy("Player 1", "Men", All, "Heal_Beacon", 100);
    PreserveTrigger();
}
""")

    # -------------------------------------------------------------
    # 3. Civilian Gacha System (1 Civilian -> 1 Random Unit)
    # -------------------------------------------------------------
    units = [
        "Terran Marine",
        "Terran Firebat",
        "Terran Ghost",
        "Protoss Zealot",
        "Protoss Dragoon",
        "Zerg Zergling",
        "Zerg Hydralisk"
    ]

    for idx, unit in enumerate(units, 1):
        triggers.append(f"""
Trigger("Player 1"){{
Conditions:
    Bring("Player 1", "Terran Civilian", "Gacha_Beacon", At Least, 1);
    Switch("Gacha_Switch_{idx}", Set);

Actions:
    RemoveUnitAt("Player 1", "Terran Civilian", 1, "Gacha_Beacon");
    CreateUnit("Player 1", "{unit}", 1, "Spawn_Location");
    SetSwitch("Gacha_Switch_{idx}", Clear);
    DisplayText("Gacha Success! Created [{unit}]", 4);
    PreserveTrigger();
}}
""")

    # -------------------------------------------------------------
    # 4. Hero Combination System (2 Units -> 1 Hero / Max 1 Limit)
    # -------------------------------------------------------------
    hero_combinations = [
        ("Terran Marine", "Jim Raynor (Marine)"),
        ("Terran Firebat", "Gui Montag (Firebat)"),
        ("Terran Ghost", "Alexei Stukov (Ghost)"),
        ("Protoss Zealot", "Fenix (Zealot)"),
        ("Protoss Dragoon", "Fenix (Dragoon)"),
        ("Zerg Zergling", "Devouring One (Zergling)"),
        ("Zerg Hydralisk", "Hunter Killer (Hydralisk)")
    ]

    for base_unit, hero_unit in hero_combinations:
        triggers.append(f"""
Trigger("Player 1"){{
Conditions:
    Bring("Player 1", "{base_unit}", "Combine_Beacon", At Least, 2);
    Command("Player 1", "{hero_unit}", Exactly, 0);

Actions:
    RemoveUnitAt("Player 1", "{base_unit}", 2, "Combine_Beacon");
    CreateUnit("Player 1", "{hero_unit}", 1, "Hero_Spawn_Location");
    DisplayText("Hero [{hero_unit}] Joined the Battlefield!", 4);
    PreserveTrigger();
}}
""")

    # -------------------------------------------------------------
    # 5. Base Safety System (Kill Enemy Trespassers)
    # -------------------------------------------------------------
    triggers.append("""
Trigger("All Players"){
Conditions:
    Bring("Bad Guys", "Men", "Base_Safety_Zone", At Least, 1);

Actions:
    RemoveUnitAt("Bad Guys", "Men", All, "Base_Safety_Zone");
    PreserveTrigger();
}
""")

    # Save to file
    output_filename = "map_triggers.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.writelines(triggers)

    print(f"Success! Output generated at '{output_filename}'.")

if __name__ == "__main__":
    generate_triggers()