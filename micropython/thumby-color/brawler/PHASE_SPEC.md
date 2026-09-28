# Phase 07: Game Feel & Impact Juice Specification

This document contains localized context and technical specifications for the feature/brawler-feel branch.

---

## 1. Scope & Core Objectives
- Hitstop (Frame Freeze): Momentary 2~4 frame execution lock on impact to deliver tactile feedback
- Camera Shake: Directional Screen Offset Jitter decay on heavy hits and finishers
- Impact FX Particles: Burst spark visual rendering on successful collision

---

## 2. Technical Architecture

### A. Impact Feedback Pipeline
  [ Hit Collision Detected ] ---> Trigger Hitstop (Freeze 3 frames)
                              ---> Trigger Camera Shake (Intensity: 4px decay)
                              ---> Spawn Impact Spark FX (12 frames lifespan)

### B. Module Breakdown
- engine/camera.py: Camera Shake offset calculation with trapezoidal decay
- engine/hitbox.py: Hitstop freeze trigger dispatch on impact resolution
- gfx/renderer.py: Screen jitter application and Impact FX rendering

---

## 3. Sub-Task Checklist
- [ ] Add Hitstop frame delay manager in engine/hitbox.py
- [ ] Add camera shake offset and intensity decay logic in engine/camera.py
- [ ] Render Screen Shake offset in gfx/renderer.py
- [ ] Add hit impact spark visualizers