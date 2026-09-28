# Project: Thumby Color Metroidvania (Aria of Sorrow Style)

## Hardware & Environment Specifications
- **MCU:** Raspberry Pi RP2350 (520KB RAM, External Flash)
- **Display:** 128x128 LCD, 12-bit/16-bit Color, Target 30 FPS
- **Language/Runtime:** MicroPython
- **Repository:** `JIHOON-PROJECTS`
- **Path:** `thumby-color/metroidvania/`
- **Code Style:** Pure English code and comments ONLY.

## Core System Architecture & Pillars
1. **Map Exploration (100%):** 128x128 room streaming with bitmask tracking.
2. **Collection Pillars (100%):**
   - **Weapons:** Unique hitboxes and ranges.
   - **Armor:** Defense and stat boosts.
   - **Accessories:** Skill/passive effects (Slot system: 1 to 3 max equipped).
3. **Drop Mechanics:** LUCK stat boosts enemy item/accessory drop rates.

## Progress & Branch Structure
- `feature/thumby-metroidvania` (Main Spec Branch)
  - `feature/m1-engine` -> Merged (Player AABB Physics, Hitbox, Room Streamer)
  - `feature/m2-enemy` -> Merged (Enemy FSM, LUCK Drop System)
  - `feature/m3-ui` -> Merged (128x128 Compact HUD, Equipment/Accessory Menu)
  - `feature/m4-save` -> Merged (RP2350 Flash Struct Serialization Driver)

## Current Source Code Directory Layout
- `src/engine/physics.py` (Player movement, gravity, AABB tile collision)
- `src/engine/hitbox.py` (Weapon hitbox relative to player facing direction)
- `src/engine/streamer.py` (128x128 room transitions & exploration tracking)
- `src/entities/enemy.py` (Patrol/Chase enemy FSM)
- `src/systems/drop.py` (Luck-modified drop table calculator)
- `src/systems/ui.py` (HUD & 5-row Equipment cursor menu)
- `src/systems/save.py` (Flash binary struct packing/unpacking)

## Next Immediate Tasks
1. Merge `feature/m4-save` into `feature/thumby-metroidvania`.
2. Create `main.py` integration loop and `tests/test_engine.py` unit tests in `feature/thumby-metroidvania` branch for PC/emulator testing.
3. Build item database (`src/data/items.py`) for weapons, armors, and accessories.

"이건 내 Thumby Color 메트로배니아 프로젝트의 최신 Context 파일이야. 위 docs/context.md 내용을 바탕으로 feature/thumby-metroidvania 브랜치에 들어갈 통합 main.py와 tests/test_engine.py 코드를 순수 영문으로 작성해 줘."