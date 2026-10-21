# SRPG-v1 work note

- Branch: `feature/thumby-srpg-v1`, isolated from `epic/thumby-growth` at `e899970`.
- Scope: new `micropython/Thumby/SRPG-v1/` and its preview/docs; existing Fight/Growth files stay untouched.
- Target: standard 72×40 monochrome Thumby; 15×10 map, 9×5 viewport, 6 allied mechs plus one battleship, 8 enemies in M1.
- Draft scale: four missions in the campaign plan; M1 is currently playable. See `THUMBY_SRPG_V1_DRAFT.md`.
- Art direction: original 1-bit mini unit silhouettes and three 360-byte VLSB manga still cut-ins (REAL, SUPER, SHIP), followed by miniature weapon effects.
- Art follow-up: user supplied Game Boy pixel-art screenshots as a style reference. Replaceable 16×16 prototypes include RV (square REAL helmet, antenna, and long beam rifle), SG (broad horned SUPER based on the user sketch), SM (SUPER with a carved X chest), and ST (SUPER with a distinct crest/shoulder profile). IDs are RV/RZ/RF and SG/SM/ST. Keep human-like separated limbs and square armor; avoid exact franchise copies and the round enemy-like first draft. Combat hides HP/EN during action. Ranged attacks add a short recoil; fist/saber attacks lunge, hit, and recover. SUPER loadouts have one basic melee, two basic shots, one unique ranged finisher, and one unique melee finisher. Review `docs/personal-game-ai/assets/srpg-v1-pixel-mech-sprites.svg`. Next Work should refine the four silhouettes, then draw RZ/RF and any missing mechs in the sprite editor. Animated mock preview was generated for this conversation.
- Battleship is fixed on the base tile, has range 5 and 100 HP, and its HP mirrors the base-defense counter.
- Weapon implementation: at most five per unit; SUPER uses three basic weapons plus two finishers, REAL uses shared Vulcan/beam saber/beam gun-or-rifle slots plus one unique finisher (four total). The M1 weapon menu selects per-unit power/range and applies weapon-specific range and damage.
- Status implementation: map summary shows HP, EN, and armor; the detail screen adds mobility and movement. Weapon power/range is shown in weapon selection. No separate hit/evasion values. EN costs remain undecided.
- Verification: rules and display mock tests; hardware FPS and readability are not verified.


## UI, content scale and performance follow-up
- Parent: `feature/thumby-srpg-v1`. Child: `work/thumby-srpg-v1-ui-capacity-20261021`.
- The 72×40 screen limits simultaneous information and animation framing; it does not set the roster or campaign ceiling. Decide total unit/mission counts from game scope and measured flash/RAM budgets. The four-mission plan remains an initial draft, not a display-imposed final cap.
- The tactical map is 15×10 tiles; show a full-screen 9×5 viewport. Do not reserve a persistent side panel for stats. Selecting a unit opens its command menu; `STATUS` is the detailed readout.
- Keep the compact status vocabulary to HP, EN, mobility (MOB), armor (ARM), and weapons. Weapon choice shows name, power, and range. Movement range belongs to the map/Move interaction; avoid adding hit/evasion and other secondary fields without a gameplay need.
- Keep 16×16 unit battle silhouettes. During a normal attack, prioritize both units, the relevant weapon effect, and HP result; reserve the 72×40 cut-in for finishers. Keep ordinary attack animation brief and skippable.
- Performance direction: measure on standard Thumby before setting a final target. Current SRPG code requests 20 FPS; profile a 30 FPS target with a representative full map, unit count, and attack. Draw static map layers only when state changes where practical, avoid repeated per-frame allocations, and load only active mission data if memory pressure appears. Keep authored content in flash and transient state in RAM.
- Hardware and current implementation facts: Thumby has 2 MB storage and a 72×40 monochrome OLED; RP2040 has 264 KB SRAM. A packed one-bit 72×40 image is 360 bytes, excluding MicroPython/runtime and other buffers. Storage supports larger content sets, but actual map/campaign capacity still requires measurement.
- Current implementation remains the M1 prototype: six allied mechs, one battleship, eight enemies; only M1 is playable. No roster or campaign expansion, UI implementation, optimization, or hardware benchmark is included in this documentation change.
- Completion criteria for the follow-up: implement the 9×5 viewport and the agreed compact status/weapon presentation; verify map navigation, menus, combat and special cut-ins in emulator; run existing unit/UI tests; measure FPS and memory on physical Thumby under representative load; report any remaining bottleneck before setting final content targets.
- Current state: documentation records the user-approved direction; implementation and physical-device performance remain pending.
