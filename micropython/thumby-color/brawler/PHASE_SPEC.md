# Phase 10: Item, Shop & Skill Scroll System Specifications

## 1. Objective
Implement the item economy and RPG progression system: Field Pickups (Coins/Health/Throwables), Weapon Durability, and the Town Shop for purchasing skill scrolls and upgrading attributes.

## 2. Deliverables & Modules

### A. Field Item & Pickup Pipeline (`entities/item.py`)
- Coins, Health Consumables, and Temporary Throwable Weapons
- Y-sorting world placement & collision pickup triggers (`3D Volume Overlap`)

### B. Weapon Durability & Lifecycle Engine (`engine/weapon.py`)
- Limited hit/use durability counters for equipped weapons
- Custom weapon attack hitboxes & destruction state on durability depletion

### C. Town Shop & Skill Scroll UI (`ui/shop.py`)
- Compact town store interface optimized for 128x128 screen
- Spend coins to unlock new combo skill scrolls and upgrade player ATK/HP stats

### D. Skill Scroll Inventory & Equipment Handler (`engine/skill_manager.py`)
- Dynamic skill scroll mapping to specific controller button combinations

## 3. Verification Checklist
- [ ] Field items drop from broken props/enemies and are collected via collision.
- [ ] Equipped weapons track durability and break after max uses.
- [ ] Town Shop UI renders correctly and handles coin transactions.
- [ ] Purchased skill scrolls correctly modify player combat combo behavior.
- [ ] Maintains 30 FPS sync and MicroPython memory stability on RP2040.