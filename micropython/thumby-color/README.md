# Thumby Color Projects

A collection of retro handheld games and engine modules built for the **Thumby Color** (RP2040 MicroPython).

## Hardware Specifications
- **Display:** 0.85-inch Color TFT Display (128x128 Resolution, RGB565)
- **MCU:** Raspberry Pi RP2040
- **Language:** MicroPython
- **Input:** 4-way D-Pad, A/B Action Buttons

## Project Architecture

| Module | Genre & Mechanics | Key Features |
| :--- | :--- | :--- |
| `brawler/` | 2.5D Belt-Scroll Action | Y-sorting depth rendering, hitboxes, combat state machine |
| `srpg/` | Turn-Based Tactical RPG | Grid-based movement, tactical AI, battle transition screens |
| `rhythm/` | Rhythm Action | Timing-based input judgment, scrolling note lane rendering |
| `platformer/` | Side-Scrolling Action | Gravity physics, platform collision, tilemap scrolling |
| `fighting/` | 2D Versus Fighting | Frame-based attack input, collision detection, health HUD |

## How to Run
1. Connect your Thumby Color via USB.
2. Load the desired module's `main.py` directly onto the device using the Thumby Web IDE or MicroPython toolchain.