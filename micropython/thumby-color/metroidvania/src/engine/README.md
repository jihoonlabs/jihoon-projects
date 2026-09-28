# M1 Engine Module

## Focus
1. **Player Physics & AABB Tile Collision:** Walk, jump, gravity, boundary.
2. **Weapon Hitbox System:** Attack trajectory & range calculation.
3. **128x128 Room Streaming:** Trigger door transition & Flash streaming logic.
4. **Map Exploration Bitmask Tracker:** Track visited 128x128 rooms.

## File Structure
- `src/engine/physics.py` (or .c)
- `src/engine/streamer.py`
- `src/engine/hitbox.py`