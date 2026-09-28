# Phase 12: Audio Visual Polish & Final Release Specifications

## 1. Objective
Implement standard audio audio-visual feedback loops: Thumby Buzzer Chiptune SFX/BGM sound pipeline, Main Title Screen with game start/continue mechanics, and final 30 FPS RP2040 MicroPython release optimizations.

## 2. Deliverables & Modules

### A. Audio Sound Engine (`engine/audio.py`)
- Non-blocking tone generator for Thumby Color Piezo Buzzer
- Sound FX presets (Hit sound, Gunshot, Coin pickup, Slash, Skill sound, Game Over tone)
- Lightweight 8-bit Chiptune loop background music driver

### B. Title Screen & Game State Manager (`ui/title.py`)
- Retro Oriental Brawler Title Screen with "NEW GAME" / "CONTINUE" menu
- High Score / Progression data linkage to Phase 11 Save Manager

### C. Visual Polish & HUD Finalization
- Screen Flash effects on Heavy Hits / Musket Gunshots
- Final memory cleanup & GC optimization check for stable 30 FPS sync

## 3. Verification Checklist
- [ ] Sound FX triggers do not freeze or cause frame drops during combat.
- [ ] Title Screen correctly loads saved progress on "CONTINUE" selection.
- [ ] Screen flash and hitstop sync cleanly on heavy strikes.
- [ ] Maintains stable 30 FPS with < 128KB GC allocation footprint.