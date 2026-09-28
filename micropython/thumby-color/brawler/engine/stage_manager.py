# engine/stage_manager.py
# Phase 08: Stage & Wave Management Module
# Handles camera deadzone locking, enemy spawning triggers, and wave clear detection.

class StageManager:
    # Stage States
    STATE_PROGRESS = 0    # Moving freely along the stage
    STATE_DIALOGUE = 1    # Dialogue overlay active (Entities paused)
    STATE_WAVE_LOCKED = 2 # Camera locked, defeating wave enemies
    STATE_CLEAR = 3       # Stage clear sequence

    def __init__(self, stage_data, camera, enemy_factory=None):
        self.stage_data = stage_data
        self.camera = camera
        self.enemy_factory = enemy_factory # Function or class to spawn enemy instances

        self.state = self.STATE_PROGRESS
        self.current_wave_index = 0
        self.active_enemies = []
        
        # UI Signal flags
        self.show_go_indicator = False
        self.current_dialogue = None

    def update(self, player, world_enemies):
        """
        Main tick method called every frame (30 FPS sync).
        """
        self.active_enemies = [e for e in world_enemies if getattr(e, 'hp', 0) > 0]

        if self.state == self.STATE_PROGRESS:
            self._check_wave_triggers(player)
            self._check_stage_clear(player)

        elif self.state == self.STATE_WAVE_LOCKED:
            self._update_wave_lock(player)

    def _check_wave_triggers(self, player):
        """Checks if player reached the next wave trigger position."""
        waves = self.stage_data.get("waves", [])
        if self.current_wave_index >= len(waves):
            return

        current_wave = waves[self.current_wave_index]
        trigger_x = current_wave["trigger_x"]

        # Player reached or passed the trigger boundary
        if player.x >= trigger_x:
            self._start_wave(current_wave)

    def _start_wave(self, wave_spec):
        """Locks camera and spawns wave enemies."""
        self.state = self.STATE_WAVE_LOCKED
        self.show_go_indicator = False

        # Lock camera boundaries to current arena
        lock_x = wave_spec["camera_lock_x"]
        screen_w = self.stage_data["screen_width"]
        self.camera.set_lock_bounds(min_x=lock_x, max_x=lock_x)

        # Check for dialogue before wave
        if wave_spec.get("dialogue_before"):
            self.current_dialogue = wave_spec["dialogue_before"]
            # FSM transition to dialogue state handled by Game Controller

        # Spawn Enemies via Factory
        if self.enemy_factory:
            for spec in wave_spec["enemies"]:
                spawn_x = lock_x + spec["rel_x"]
                spawn_y = spec["y"]
                self.enemy_factory(spec["type"], spawn_x, spawn_y, spec["dir"])

    def _update_wave_lock(self, player):
        """Monitors remaining active enemies in current wave."""
        if len(self.active_enemies) == 0:
            # Wave cleared!
            self._on_wave_cleared()

    def _on_wave_cleared(self):
        """Unlocks camera and triggers GO! indicator."""
        waves = self.stage_data["waves"]
        current_wave = waves[self.current_wave_index]

        # Check for dialogue after wave
        if current_wave.get("dialogue_after"):
            self.current_dialogue = current_wave["dialogue_after"]

        # Unlock Camera to full stage bounds
        self.camera.unlock_bounds(max_x=self.stage_data["world_width"] - self.stage_data["screen_width"])

        # Enable "GO!" direction UI & advance wave index
        self.show_go_indicator = True
        self.state = self.STATE_PROGRESS
        self.current_wave_index += 1

    def _check_stage_clear(self, player):
        """Checks if player reached the stage end boundary."""
        if player.x >= self.stage_data["clear_x"]:
            self.state = self.STATE_CLEAR
            self.show_go_indicator = False

    def on_player_move_forward(self):
        """Called when player advances right after wave clear to hide GO! arrow."""
        if self.show_go_indicator:
            self.show_go_indicator = False