# Metroidvania System Architecture

## Target HW
- MCU: RP2350 (520KB RAM, Flash)
- Display: 128x128 LCD | FPS: 30

## Module Specs

### M1. Engine & Room Streaming
- 128x128 px room-based Flash streaming.
- AABB tile collision & entity hitboxes.

### M2. Combat & Soul System
- Entity FSM (Player/Enemy).
- LCK-based Soul drop algorithm.
- Soul Types: Bullet (MP spell), Guardian (Cont. MP), Enchant (Passive).

### M3. UI Engine
- In-game minimal HUD (HP/MP).
- Paused menu state for equip & soul binding.

### M4. Flash Persistence
- Serialize `PlayerSaveState` struct into RP2350 Flash sector.
- Save stats, unlocked souls bitmask, map flags.

## Layout
`src/` (`engine/`, `entities/`, `systems/`) | `assets/`