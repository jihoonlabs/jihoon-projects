# SRPG-v1 work note

- Branch: `feature/thumby-srpg-v1`, isolated from `epic/thumby-growth` at `e899970`.
- Scope: new `micropython/Thumby/SRPG-v1/` and its preview/docs; existing Fight/Growth files stay untouched.
- Target: standard 72×40 monochrome Thumby; 15×10 map, 5×5 viewport, 6 allied mechs plus one battleship, 8 enemies in M1.
- Draft scale: four missions in the campaign plan; M1 is currently playable. See `THUMBY_SRPG_V1_DRAFT.md`.
- Art direction: original 1-bit mini unit silhouettes and three 360-byte VLSB manga still cut-ins (REAL, SUPER, SHIP), followed by miniature weapon effects.
- Battleship is fixed on the base tile, has range 5 and 100 HP, and its HP mirrors the base-defense counter.
- Verification: rules and display mock tests; hardware FPS and readability are not verified.
