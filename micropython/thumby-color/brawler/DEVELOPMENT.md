# Period Action Brawler Engine

A 2.5D belt-scroll action RPG/Brawler engine built for **Thumby Color** (128x128 RGB565 RP2040 MicroPython).

## Concept & Architecture
- **Theme:** Classic Period Action & Exploration (Generic Oriental setting with no Japanese-specific visual elements)
- **Core Progression:** Town travel, shop skill purchases, custom combo chains, weapon durability, stage hazards
- **Engine Capabilities:** 30 FPS locked sync, Y-sorting depth rendering, frame-based hitboxes, state-machine AI

---

## Progress Overview

| Phase | Title | Branch | Status |
| :--- | :--- | :--- | :---: |
| **01** | Core Engine & Screen Scrolling | `feature/brawler-core` | `[ ]` |
| **02** | 2D Movement & Jump Physics | `feature/brawler-physics` | `[ ]` |
| **03** | Hitbox & Impact Pipeline | `feature/brawler-hitbox` | `[ ]` |
| **04** | Combat State Machine | `feature/brawler-combat-fsm` | `[ ]` |
| **05** | In-Game Debug Visualizer | `feature/brawler-debug` | `[ ]` |
| **06** | Enemy AI Framework | `feature/brawler-enemy-ai` | `[ ]` |
| **07** | Combat Juice & Game Feel | `feature/brawler-game-feel` | `[ ]` |
| **08** | Stage & Wave Lock System | `feature/brawler-stage` | `[ ]` |
| **09** | Boss Battle Logic | `feature/brawler-boss` | `[ ]` |
| **10** | Item & Shop System | `feature/brawler-items` | `[ ]` |
| **11** | Pixel Sprites & Chiptune Audio | `feature/brawler-polish` | `[ ]` |
| **12** | Save Data & Performance | `feature/brawler-optimization` | `[ ]` |

---

## Technical Specifications

### Phase 01: Core Engine & Screen Scrolling
- **Branch:** `feature/brawler-core`
- [x] **Frame Control:** Stable 30 FPS display sync loop via MicroPython ticks
- [x] **2D Depth Ordering:** Classic Y-sorting (entities drawn in order of Y-position)
- [x] **Camera Scroll:** Smooth horizontal stage scrolling following the player

### Phase 02: 2D Movement & Jump Physics
- **Branch:** `feature/brawler-physics`
- [ ] **8-Way Walking:** Responsive directional movement across the street plane
- [ ] **Jump Trajectory:** Arc jump physics with ground landing checks
- [ ] **Stage Boundaries:** Y-axis street limits (top/bottom walls)

### Phase 03: Hitbox & Impact Pipeline
- **Branch:** `feature/brawler-hitbox`
- [ ] **Hitbox Overlap:** X/Y distance overlap checks for attacks
- [ ] **Hit Reaction:** Directional knockback and hitstun frame pauses

### Phase 04: Combat State Machine
- **Branch:** `feature/brawler-combat-fsm`
- [ ] **FSM Architecture:** States (`IDLE`, `WALK`, `ATTACK`, `JUMP`, `HIT`, `DOWN`)
- [ ] **Combo Branching:** Light $\rightarrow$ Heavy $\rightarrow$ Finisher sequential input buffers
- [ ] **Special Skill:** Area-of-Effect (AoE) emergency break consuming HP

### Phase 05: In-Game Debug Visualizer
- **Branch:** `feature/brawler-debug`
- [ ] **Hitbox Overlay:** Toggleable visual debug boxes (Red: Attack, Green: Hurtbox)
- [ ] **State & FPS Counter:** Real-time entity state display and frame-rate monitor
- [ ] **Invincibility Toggle:** GOD mode testing trigger for rapid debugging

### Phase 06: Enemy AI Framework
- **Branch:** `feature/brawler-enemy-ai`
- [ ] **FSM AI System:** States (`PATROL`, `APPROACH`, `ALIGN`, `ATTACK`, `STUN`)
- [ ] **Spatial Alignment:** AI positioning along $Y$-depth before attacking
- [ ] **Enemy Archetypes:** Melee brawler, ranged attacker, and heavy super-armor unit

### Phase 07: Combat Juice & Game Feel
- **Branch:** `feature/brawler-game-feel`
- [ ] **Hitstop (Freeze Frames):** Micro-pauses on contact to amplify impact feel
- [ ] **Camera Shake:** Dynamic screen offsets on heavy attacks or finishers
- [ ] **Impact Effects:** Color-flashing impact sprites and floating combat text

### Phase 08: Stage & Wave Lock System
- **Branch:** `feature/brawler-stage`
- [ ] **Parallax Scrolling:** Multi-layer background rendering for depth
- [ ] **Arena Triggers:** Locked screen waves requiring enemy defeat to advance
- [ ] **Interactive Props:** Destructible objects dropping health or temporary weapons

### Phase 09: Boss Battle Logic
- **Branch:** `feature/brawler-boss`
- [ ] **Phase Transitions:** Dynamic behavior shifts triggered at HP thresholds
- [ ] **Super Armor:** Stun resistance during heavy boss attack animations
- [ ] **Telegraphed Attacks:** Visual floor indicators prior to high-damage skills

### Phase 10: Item & Shop System
- **Branch:** `feature/brawler-items`
- [ ] **Pickup Logic:** Health consumables and throwable melee weapons
- [ ] **Weapon Lifecycle:** Limited durability and custom attack hitboxes for weapons
- [ ] **Town Shop:** Purchasing skill scrolls and stat upgrades using coins

### Phase 11: Pixel Sprites & Chiptune Audio
- **Branch:** `feature/brawler-polish`
- [ ] **RGB565 Sprites:** Animated character and enemy pixel bitmap pipeline
- [ ] **Chiptune Audio:** Sound effects (SFX) for hits, jumps, and UI cues
- [ ] **HUD Interface:** Dynamic health bars, combo count overlays, and status text

### Phase 12: Save Data & Performance
- **Branch:** `feature/brawler-optimization`
- [ ] **Flash Persistence:** Save/Load high scores and unlocked stage states to RP2040 Flash
- [ ] **Memory Management:** Scheduled garbage collection sweeps to prevent MicroPython OOM
- [ ] **Profiler:** Maintaining locked 30 FPS performance under high entity counts