# Phase 04: Combat State Machine Specification

This document contains localized context and technical specifications for the feature/brawler-combat-fsm branch.

---

## 1. Scope & Core Objectives
- FSM Architecture: Entity state machine management (IDLE, WALK, ATTACK, JUMP, HIT, DOWN)
- Combo Branching: Sequential input buffers (Light -> Heavy -> Finisher)
- Special Skill: Emergency Area-of-Effect (AoE) break skill consuming HP

---

## 2. Technical Architecture

### A. State Transition Flow
  [ IDLE / WALK ] ---> (Button A) ---> [ ATK_1 ] ---> (A within window) ---> [ ATK_2 ] ---> [ FINISHER ]
        |                                                                                         |
        +----------------------------> (Button A + B) -------------------> [ AOE_SPECIAL ] <------+

### B. Module Breakdown
- engine/fsm.py: Generic Finite State Machine base & State interface
- entities/player.py: Combo input buffer and attack animation branching
- entities/base.py: Stun, Down, and Recovery states

---

## 3. Sub-Task Checklist
- [ ] Implement FSM architecture and State handler in engine/fsm.py
- [ ] Add 3-stage combo input buffering (ATK_1, ATK_2, FINISHER) in player.py
- [ ] Implement HP-consuming AoE emergency break skill (A + B button trigger)
- [ ] Add knockback DOWN and recovery state transitions