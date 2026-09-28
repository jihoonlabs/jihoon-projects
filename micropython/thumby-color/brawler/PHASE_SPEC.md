# Phase 06: Enemy AI & Y-Axis Tracking Specification

This document contains localized context and technical specifications for the feature/brawler-ai branch.

---

## 1. Scope & Core Objectives
- Enemy FSM States: IDLE, PATROL, CHASE, ATTACK, HITSTUN, DOWN
- Y-Axis Alignment AI: Strategic positioning along the vertical depth plane before attacking
- Attack Cooldown & Range Checks: Aggression timers and spatial attack triggers

---

## 2. Technical Architecture

### A. Enemy AI Behavioral Loop
  [ IDLE / PATROL ] ---> (Player within Sight X) ---> [ Y-ALIGNMENT ]
                            |                                |
                            +<-- (Aligned Y & In Range X) <--+ ---> [ ATTACK ] ---> [ COOLDOWN ]

### B. Module Breakdown
- entities/enemy.py: Enemy AI entity class with state machine, sight ranges, and attack logic
- main.py: Dynamic entity loop updating player and AI combat interactions

---

## 3. Sub-Task Checklist
- [ ] Implement Enemy class with FSM state loops in entities/enemy.py
- [ ] Add Y-axis alignment steering logic for natural belt-scroll movement
- [ ] Add attack range detection and cooldown timer handling
- [ ] Connect enemy attack hitboxes to impact player HP/Hitstun