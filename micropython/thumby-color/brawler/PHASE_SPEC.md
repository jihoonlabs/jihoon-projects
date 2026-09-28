# Phase 09: Boss Battle Logic Specifications

## 1. Objective
Implement high-intensity boss encounter mechanics including multi-phase pattern shifts, super-armor stun resistance, and telegraphed attack indicators.

## 2. Deliverables & Modules

### A. Boss State Machine (`entities/boss.py`)
- Extends standard Enemy FSM (`IDLE`, `PATROL`, `APPROACH`, `ATTACK`, `STUN`, `SUPER_ARMOR`, `PHASE_CHANGE`)
- Boss HP threshold checks (Phase 1 -> Phase 2 transition at <= 50% HP)

### B. Super Armor & Resistance System
- Ignore hitstun/knockback when executing heavy boss animations
- Visual aura flash / color pulse when Super Armor is active

### C. Telegraphed Attack Indicator (`gfx/telegraph.py`)
- Ground hazard indicators (red outline/fill boxes) before high-damage AoE skills
- Charge-up frame delay giving players time to dodge vertically (Y-axis)

### D. Boss Stage Config (`data/boss_spec.py`)
- Boss stats (HP, ATK, move speed) and attack pattern probability tables

## 3. Verification Checklist
- [ ] Boss switches to Phase 2 pattern upon dropping below 50% HP.
- [ ] Super Armor prevents stun frame freeze during critical attacks.
- [ ] Ground telegraph warnings correctly render before heavy AoE attacks.
- [ ] Maintains 30 FPS sync and MicroPython memory stability on RP2040.