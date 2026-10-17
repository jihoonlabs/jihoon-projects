# ThumbyGrowth Character Design Child WORK

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/thumby-growth-character-design
parent_branch: feature/thumby-growth
role: child
status: implementation-verified-pc; awaiting-user-device-check
tested_sha: 33d3c78f95dc169626da85b65048ac7d2a6cda31
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
- User supplied device photos: スクリーンショット 2026-10-17 11.30.45.png and スクリーンショット 2026-10-17 11.31.04.png. Compared the later 12.01.23/12.01.46 attack captures against the user's Kunio-kun period-drama gameplay reference (9.25.51); both tips were blockier, and the left-facing reaches appeared one pixel shorter. After the user's real-device test, they requested the simpler bar-like limb style to better match the Kunio reference. The user's 12.24.28 Freeform sketch clarified the desired kick silhouette: remove the one-pixel connector to the planted foot, use a separate broad shoe, and send the kicking limb straight out from the torso.
- Verified that the local source snapshot's original ThumbyGrowth.py Git blob hash matched the public Epic blob 6a771e9aa7eb4419e69d1122074f5374881253fe.
- Upper-lane sprite rows were clipped with the HUD boundary before the 10/16 coordinate transform. Row clipping is now applied after scaling in screen space.
- Initial validation found that mathematically mirrored left-side attacks still blended into the reduced body, so they were difficult to see in the actual composited renderer.
- Punch uses the neutral shared body and a straight, uniform two-pixel bar; reach remains unchanged.
- Kick removes both default feet from the body frame, then draws a rounded 3/5-pixel planted shoe behind the fighter and a straight two-pixel bar directly from the torso. Both chamber and extended poses stay horizontal; the extended frame only increases reach. There is no one-pixel connector leg.
- Punch and kick reuse one small axis-aligned bar renderer with pose-specific position, orientation, and reach. Both attack poses mirror around the fighter's true half-pixel center and retain equal horizontal reach in each direction. This avoids duplicated sprite frames and drawing logic; runtime RAM reduction has not been measured.
- No attack timing, hitboxes, or gameplay values changed.

## Verification
- python3 -m py_compile ThumbyGrowth.py test_character_design.py test_attack_sprite_geometry.py: pass.
- Related graphics tests after the visibility correction and one-pixel tip refinement: test_attack_sprite_geometry, test_character_design, test_background, test_combat_readability, test_combat_feedback: 47 pass.
- Attack tests check uniform two-pixel punch/kick bars, left/right mirror symmetry and equal reach from the body center, two-frame reach, the kick's rounded support-shoe profile without a connector leg, and a straight horizontal kick bar in both frames.
- Full scratch snapshot suite: 225 discovered; 13 failures and 1 import error remain in unrelated stale gameplay/UI compatibility tests and a missing replay_demo helper. These were not modified by this graphics-only task.
- PC preview uses the actual 72x40 renderer with a Thumby test double; it is not a device capture. Real-device display/speed/heap still need user confirmation.
- No production/gameplay change outside the rendering geometry listed above.
