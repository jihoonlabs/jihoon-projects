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
| **01** | Core Engine & Screen Scrolling | `feature/brawler-core` | `[x]` |
| **02** | 2D Movement & Jump Physics | `feature/brawler-physics` | `[x]` |
| **03** | Hitbox & Impact Pipeline | `feature/brawler-hitbox` | `[x]` |
| **04** | Combat State Machine | `feature/brawler-combat-fsm` | `[x]` |
| **05** | In-Game Debug Visualizer | `feature/brawler-debug` | `[x]` |
| **06** | Enemy AI Framework | `feature/brawler-enemy-ai` | `[x]` |
| **07** | Combat Juice & Game Feel | `feature/brawler-game-feel` | `[x]` |
| **08** | Stage, Wave & Dialogue System | `feature/brawler-stage` | `[x]` |
| **09** | Boss Battle Logic | `feature/brawler-boss` | `[x]` |
| **10** | Item, Shop & Skill Scroll System | `feature/brawler-items` | `[x]` |
| **11** | Pixel Sprites & Chiptune Audio | `feature/brawler-polish` | `[x]` |
| **12** | Save Data & Performance | `feature/brawler-optimization` | `[ ]` |

---

## Technical Specifications

### Phase 01: Core Engine & Screen Scrolling
- **Branch:** `feature/brawler-core`
- [x] **Frame Control:** Stable 30 FPS display sync loop via MicroPython ticks
- [x] **2D Depth Ordering:** Classic Y-sorting (entities drawn in order of Y-position)
- [x] **Camera Deadzone:** Smooth camera scroll with deadzone & edge clamping
- [x] **Screen Culling:** Rendering optimization for off-screen entities

### Phase 02: 2D Movement & Jump Physics
- **Branch:** `feature/brawler-physics`
- [x] **8-Way Walking:** Responsive directional movement across the street plane
- [x] **Jump Trajectory:** Arc jump physics with ground landing checks
- [x] **Dash Mechanism:** Double-tap directional dash for fast travel
- [x] **Stage Boundaries:** Y-axis street limits (top/bottom walls)

### Phase 03: Hitbox & Impact Pipeline
- **Branch:** `feature/brawler-hitbox`
- [x] **Hitbox Overlap:** X/Y/Z spatial overlap checks for attacks
- [x] **Hit Reaction:** Directional knockback and hitstun frame pauses

### Phase 04: Combat State Machine
- **Branch:** `feature/brawler-combat-fsm`
- [x] **FSM Architecture:** States (`IDLE`, `WALK`, `ATTACK`, `JUMP`, `HIT`, `DOWN`)
- [x] **Combo Branching:** Light -> Heavy -> Finisher sequential input buffers
- [x] **Special Skill:** Area-of-Effect (AoE) emergency break consuming HP

### Phase 05: In-Game Debug Visualizer
- **Branch:** `feature/brawler-debug`
- [x] **Hitbox Overlay:** Toggleable visual debug boxes (Red: Attack, Green: Hurtbox)
- [x] **State & FPS Counter:** Real-time entity state display and frame-rate monitor
- [x] **Invincibility Toggle:** GOD mode testing trigger for rapid debugging

### Phase 06: Enemy AI Framework
- **Branch:** `feature/brawler-enemy-ai`
- [x] **FSM AI System:** States (`PATROL`, `APPROACH`, `ALIGN`, `ATTACK`, `STUN`)
- [x] **Spatial Alignment:** AI positioning along Y-depth before attacking
- [x] **Enemy Archetypes:** Melee brawler, ranged attacker, and heavy super-armor unit

### Phase 07: Combat Juice & Game Feel
- **Branch:** `feature/brawler-game-feel`
- [x] **Hitstop (Freeze Frames):** Micro-pauses on contact to amplify impact feel
- [x] **Camera Shake:** Dynamic screen offsets on heavy attacks or finishers
- [x] **Impact Effects:** Color-flashing impact sprites and floating combat text

### Phase 08: Stage, Wave & Dialogue System
- **Branch:** `feature/brawler-stage`
- [x] **Data-Driven Level Spec:** External stage configuration dictionaries
- [x] **Wave Triggers:** Locked screen arenas requiring enemy defeat to advance
- [x] **Dialogue Overlay:** Story dialog box with NPC portrait and text scrolling
- [x] **Interactive Props:** Destructible objects dropping health or temporary weapons

### Phase 09: Boss Battle Logic
- **Branch:** `feature/brawler-boss`
- [x] **Phase Transitions:** Dynamic behavior shifts triggered at HP thresholds
- [x] **Super Armor:** Stun resistance during heavy boss attack animations
- [x] **Telegraphed Attacks:** Visual floor indicators prior to high-damage skills

### Phase 10: Item, Shop & Skill Scroll System
- **Branch:** `feature/brawler-items`
- [x] **Pickup Logic:** Coins, health consumables, and throwable melee weapons
- [x] **Weapon Lifecycle:** Limited durability and custom attack hitboxes
- [x] **Town Shop Interface:** Menu for buying skill scrolls and upgrading stats using coins
- [x] **Skill Equipment:** Equipping purchased moves to specific button combinations

### Phase 11: Pixel Sprites & Chiptune Audio
- **Branch:** `feature/brawler-polish`
- [x] **RGB565 Sprites:** Animated character and enemy pixel bitmap pipeline
- [x] **Chiptune Audio:** Sound effects (SFX) for hits, jumps, and UI cues
- [x] **HUD Interface:** Dynamic health bars, combo count overlays, and status text

### Phase 12: Save Data & Performance
- **Branch:** `feature/brawler-optimization`
- [ ] **Flash Persistence:** Save/Load high scores, coins, and skill scroll status to Flash
- [ ] **Memory Management:** Scheduled garbage collection sweeps to prevent MicroPython OOM
- [ ] **Profiler:** Maintaining locked 30 FPS performance under high entity counts