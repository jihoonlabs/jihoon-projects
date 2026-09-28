# Retro Oriental Belt-Scroll Engine (Thumby Color)
> Target: 128x128 RGB565, RP2040 MicroPython, 30 FPS

## 1. Project Overview
A 2.5D retro oriental action engine featuring 3-step character customization, home-ground starting stages, overseas expedition branching, and 4-role stage enemies.

## 2. Integrated Architecture
- main.py: Core loop (Physics, Skill FSM, Inventory, Shop, Save, Audio, Camera Shake, Hitstop)
- data/
  - character_presets.py: Gender x Outfit (KR/CN/JP) x 7 Colors
  - stage_presets.py: Home-origin starting router & overseas branch manager
  - enemy_presets.py: 4 Enemy roles per region (Brawler, Thrower, Heavy, Boss)
- entities/enemy.py: State machine AI with 3-hit combo & projectiles
- ui/
  - character_select.py: 3-step creation screen
  - stage_branch.py: Expedition path selection screen

## 3. Quick Test Checklist
1. Title -> NEW_GAME -> Verify 3-step Char Select UI.
2. Verify Stage 1 starts at selected culture's home region (KR/CN/JP).
3. Check Brawler enemy 3-hit combo & hitstop/camera feedback.
4. Defeat Boss -> Verify Expedition Branch UI popup.
5. All .py files use 100% English comments (MicroPython encoding safety).

"Thumby Color 동양 시대극 벨트스크롤 엔진 프로젝트야. 원격 리포지토리의 feature/brawler-assets 브랜치에 최신 코드가 푸시되어 있어. DEVELOPMENT.md 참고해서 전체 아키텍처 점검하고 실기 테스트 및 후속 작업 이어가자."