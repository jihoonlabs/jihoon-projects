# Phase 08: Stage, Wave & Dialogue System Specifications

## 1. Objective
Implement the core belt-scroll progression loop: Camera Wave Lock -> Enemy Spawning -> All Defeated -> "GO!" Indicator -> Dialogue Overlay.

## 2. Deliverables & Modules

### A. Data-Driven Level Spec (`data/stage_01.py`)
- Camera lock boundaries (`trigger_x`)
- Wave specs: spawn positions, enemy types, and counts

### B. Stage & Wave Manager (`engine/stage_manager.py`)
- Player position tracking and Camera Deadzone Lock
- Enemy survival tracking (`enemies_remaining`)
- Camera unlock & "GO!" trigger on wave clear

### C. "GO! ▶" Indicator (`ui/go_indicator.py`)
- Blinking arrow indicator on right edge after wave clear
- Auto-hide when player moves towards next area

### D. Lightweight Dialogue UI (`ui/dialogue.py`)
- Compact box renderer optimized for 128x128 screen
- Typewriter text scrolling & A-button input handler
- Pause player/enemy FSMs during dialogue (`STATE_DIALOGUE`)

## 3. Verification Checklist
- [ ] Camera locks correctly at target X coordinate.
- [ ] Camera remains locked until all spawned enemies are defeated.
- [ ] "GO! ▶" indicator blinks after wave clear.
- [ ] Dialogue box freezes gameplay and handles A button input.
- [ ] Maintains 30 FPS sync and memory stability on RP2040 MicroPython.