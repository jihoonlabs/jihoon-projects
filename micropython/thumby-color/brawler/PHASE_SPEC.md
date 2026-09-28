# Phase 11: Save/Load & Progression State Specifications

## 1. Objective
Implement persistent storage using MicroPython's Flash File IO (`json`) to save and load player progression, unlocked skill scrolls, coin balance, and stage progress without GC memory bottlenecks.

## 2. Deliverables & Modules

### A. Save State Manager (`engine/save_manager.py`)
- Standardized data schema (`coins`, `max_hp`, `base_atk`, `unlocked_skills`, `current_stage_idx`, `equipped_weapon_id`)
- Flash IO safe write/read logic using MicroPython `json` library with corruption fallback

### B. Progression State Integration (`engine/progression.py`)
- Stage transition persistence (Carrying over player stats between stages)
- Game Over / Retry stat reset handler

## 3. Verification Checklist
- [ ] Progression data correctly serializes to `save_data.json` upon stage clear or shop exit.
- [ ] Game restart restores coins, unlocked skills, and stat upgrades seamlessly.
- [ ] Fallback mechanism returns default initial state if save file is missing or corrupt.
- [ ] Zero frame-drop IO execution (IO calls run outside high-frequency render loops).