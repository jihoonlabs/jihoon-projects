# ThumbyGrowth Character Design Child WORK

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/thumby-growth-character-design
parent_branch: feature/thumby-growth
role: child
status: implementation-verified-pc; awaiting-user-device-check
base_sha: 694224bd26135d2abd97f9a2a79eb0a994b72f28

## Responsibility
Fix only character rendering issues reproduced from the user's Thumby screenshots:
- Preserve fighter head/hair/body pixels when actors move into the upper depth lane.
- Make left-facing punch/kick artwork a consistent mirror of right-facing frames.
- Keep visible animation frame cadence the same in either direction.

## Boundaries
- Do not change movement/input behavior, collision, attack hitboxes, damage, cooldown/recovery, saves, map/gameplay rules, or country identity design.
- Do not change attack cooldowns to address the reported right/left timing difference; this Child only normalizes the visual frame geometry/cadence.
- Keep the existing shared body and 72x40 Thumby renderer.

## Evidence and implementation
- User supplied device photos: スクリーンショット 2026-10-17 11.30.45.png and スクリーンショット 2026-10-17 11.31.04.png.
- Verified that the local source snapshot's original ThumbyGrowth.py Git blob hash matched the public Epic blob 6a771e9aa7eb4419e69d1122074f5374881253fe.
- Upper-lane sprite rows were clipped with the HUD boundary before the 10/16 coordinate transform. Row clipping is now applied after scaling in screen space.
- Attack limbs now use a single right-facing pixel pose mirrored around the fighter centerline. Left/right frame cadence and reach are tested for punches and kicks.

## Verification
- python3 -m py_compile ThumbyGrowth.py test_character_design.py test_attack_sprite_geometry.py: pass.
- Related graphics tests: test_attack_sprite_geometry, test_character_design, test_background, test_combat_readability, test_combat_feedback: 47 pass.
- Full scratch snapshot suite: 225 discovered; 13 failures and 1 import error remain in unrelated stale gameplay/UI compatibility tests and a missing replay_demo helper. These were not modified by this graphics-only task.
- PC preview uses the actual 72x40 renderer with a Thumby test double; it is not a device capture. Real-device display/speed/heap still need user confirmation.
- No production/gameplay change outside the rendering geometry listed above.
