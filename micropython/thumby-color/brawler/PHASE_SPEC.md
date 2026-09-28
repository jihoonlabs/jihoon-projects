# Phase 05: In-Game Debug Visualizer Specification

This document contains localized context and technical specifications for the feature/brawler-debug branch.

---

## 1. Scope & Core Objectives
- Hitbox Overlay: Toggleable visual debug boxes (Red: Attack, Green: Hurtbox, Blue: Z-Height)
- State & Telemetry Monitor: Real-time entity state, memory usage, and locked FPS counter
- GOD Mode Trigger: Invincibility toggle switch for rapid combat testing

---

## 2. Technical Architecture

### A. Debug Overlay Control
  [ SELECT Button Toggle ] ---> [ DEBUG_LEVEL_0: Clean HUD ]
                           ---> [ DEBUG_LEVEL_1: FPS & State Telemetry ]
                           ---> [ DEBUG_LEVEL_2: Full Hitbox/Hurtbox Wireframes ]

### B. Module Breakdown
- engine/debug.py: Telemetry collector, memory profiler & overlay toggle
- gfx/renderer.py: Conditional wireframe hitbox drawing routines
- entities/player.py: GOD mode invincibility flag and toggle switch

---

## 3. Sub-Task Checklist
- [ ] Implement DebugManager and profile telemetry in engine/debug.py
- [ ] Add SELECT button debug view level toggle switch
- [ ] Implement conditional Hitbox/Hurtbox/Z-Height wireframe rendering in renderer.py
- [ ] Add GOD mode invincibility toggle for player testing