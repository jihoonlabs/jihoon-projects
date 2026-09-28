# data/stage_01.py
# Phase 08: Data-Driven Stage Specification for Stage 01
# Lightweight data structure optimized for RP2040 MicroPython

STAGE_01_DATA = {
    "stage_id": "stage_01",
    "title": "Town Outskirts",
    "world_width": 640,       # Total stage length along X-axis
    "screen_width": 128,      # Thumby Color screen width
    "screen_height": 128,     # Thumby Color screen height
    "ground_y_min": 80,       # Top boundary for Y-sorting street plane
    "ground_y_max": 120,      # Bottom boundary for Y-sorting street plane
    
    # Sequence of triggers and waves in Stage 01
    "waves": [
        {
            "wave_id": 1,
            "trigger_x": 160,       # When camera reaches X=160, lock camera & trigger wave
            "camera_lock_x": 160,    # Camera deadzone scroll locks at this X
            "enemies": [
                # (enemy_type, spawn_x_offset, spawn_y, initial_direction)
                # spawn_x_offset is relative to camera_lock_x
                {"type": "BRAWLER", "rel_x": -20, "y": 95, "dir": 1},
                {"type": "BRAWLER", "rel_x": 138, "y": 105, "dir": -1},
            ],
            "dialogue_before": [
                {"speaker": "HERO", "text": "Halt! Who goes there?"},
                {"speaker": "BANDIT", "text": "Leave your coins and run!"}
            ],
            "dialogue_after": None  # No dialogue after wave 1
        },
        {
            "wave_id": 2,
            "trigger_x": 340,
            "camera_lock_x": 340,
            "enemies": [
                {"type": "BRAWLER", "rel_x": -15, "y": 88, "dir": 1},
                {"type": "RANGED", "rel_x": 135, "y": 115, "dir": -1},
                {"type": "HEAVY", "rel_x": 145, "y": 98, "dir": -1},
            ],
            "dialogue_before": None,
            "dialogue_after": [
                {"speaker": "HERO", "text": "Clear! Let's keep moving forward."}
            ]
        }
    ],

    # Stage End Boundary
    "clear_x": 512  # X-coordinate to trigger stage clear sequence
}