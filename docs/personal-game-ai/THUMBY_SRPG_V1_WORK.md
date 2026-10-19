# SRPG-v1 work note

- Branch: `feature/thumby-srpg-v1`, isolated from `epic/thumby-growth` at `e899970`.
- Scope: new `micropython/Thumby/SRPG-v1/` and its preview/docs; existing Fight/Growth files stay untouched.
- Target: standard 72×40 monochrome Thumby; 15×10 map, 5×5 viewport, 6 allied mechs plus one battleship, 8 enemies in M1.
- Draft scale: four missions in the campaign plan; M1 is currently playable. See `THUMBY_SRPG_V1_DRAFT.md`.
- Art direction: original 1-bit mini unit silhouettes and three 360-byte VLSB manga still cut-ins (REAL, SUPER, SHIP), followed by miniature weapon effects.
- Art follow-up: user supplied Game Boy pixel-art screenshots as a style reference. R1 and S1 have replaceable 16×16 prototypes. Latest direction: both allies should read as humanoid, with separated limbs and square armor; REAL stays slim with a visible weapon, SUPER is broader with a horn crest and blocky torso. Avoid the round, oversized enemy-like silhouette in the first draft. During combat, hide HP/EN; show them before and after. Review `docs/personal-game-ai/assets/srpg-v1-pixel-mech-sprites.svg`. Next Work should review the latest silhouettes at native 16×16, refine from user feedback, then draw the remaining units in the sprite editor. Animated mock preview was generated for this conversation.
- Battleship is fixed on the base tile, has range 5 and 100 HP, and its HP mirrors the base-defense counter.
- Weapon implementation: at most five per unit; SUPER uses three basic weapons plus two finishers, REAL uses shared Vulcan/beam saber/beam gun-or-rifle slots plus one unique finisher (four total). The M1 weapon menu selects per-unit power/range and applies weapon-specific range and damage.
- Status implementation: map summary shows HP, EN, and armor; the detail screen adds mobility and movement. Weapon power/range is shown in weapon selection. No separate hit/evasion values. EN costs remain undecided.
- Verification: rules and display mock tests; hardware FPS and readability are not verified.
