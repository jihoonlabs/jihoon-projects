# Phase 03: Hitbox & Impact Pipeline Specification

This document contains localized context and technical specifications for the feature/brawler-hitbox branch.

---

## 1. Scope & Core Objectives
- Volume Hitbox Overlap: 3D spatial bounding check (dX <= 16, dY <= 8, dZ <= 12)
- Hurtbox & Active Frames: Frame-based attack activation windows
- Hit Reaction & Knockback: Velocity impulse application on impact
- Hitstun & Invincibility (i-frames): Temporary state locks during hit reactions

---

## 2. Technical Architecture

### A. Hitbox Volume Matrix
  [ Attacker (X1, Y1, Z1) ] ---------- Overlap Test ---------- [ Victim (X2, Y2, Z2) ]
   - Attack Range: 16px                                         - Hitbox Width: 12px
   - Depth Tolerance: 8px                                       - Depth Tolerance: 8px
   - Height Reach: 12px                                         - Height Reach: 16px

### B. Module Breakdown
- engine/hitbox.py: Spatial overlap calculator & damage resolution
- entities/player.py: Attack trigger & active frame management

---

## 3. Sub-Task Checklist
- [ ] Implement VolumeHitbox spatial overlap checker in engine/hitbox.py
- [ ] Add attack button input (Button A) with frame-based active windows in player.py
- [ ] Add hitstun & directional knockback state handling for targets
- [ ] Visual debug display for hitboxes (Red: Attack, Green: Hurtbox)