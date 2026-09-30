# Thumby Color MicroPython 2D Brawler 게임 엔진 핵심 리뷰 (ANALYSIS_BRAWLER_GAME.md)

## 1. 개요 (Overview)
본 문서는 `feature/brawler` 브랜치의 MicroPython 기반 임베디드 2D 레트로 액션 밸트스크롤(Brawler) 게임 엔진(`micropython/thumby-color/brawler`) 코드에 대한 구조 분석 및 성능/조작감/메모리 관점의 리뷰 보고서입니다.

---

## 2. 🌟 잘 구현된 부분 (Positive Note)

* **3D 레인(Lane) 기반 히트박스 판정 (`hitbox.py`)**:
  * 단순 2D AABB가 아닌 `X`(전방 거리), `Y`(Z-인덱스/깊이 레인), `Z`(점프 높이) 축을 모두 계산하는 3차원 볼륨 히트박스(`VolumeHitbox`) 판정을 구현하여 밸트스크롤 특유의 입체 타격감을 잘 구현함.
* **Hitstop & Screen Shake 시각/손맛 피드백**:
  * 타격 성공 시 순간적으로 프레임을 멈추는 `hitstop_frames` 및 카메라이펙트(`shake_power`)가 잘 연결되어 있음.
* **MicroPython 타이머 안전 처리**:
  * `DoubleTapDetector`에서 `time.ticks_diff()`를 사용하여 임베디드 틱 오버플로우를 안전하게 방지함.

---

## 3. ⚠️ 성능 및 런타임/조작감 필수 개선 항목 (Critical Issues)

### 1) 매 공격 시 객체 생성으로 인한 MicroPython GC(Garbage Collector) 병목 (Performance)
* **대상**: `player.py` (`trigger_attack`, `trigger_special`)
* **현상**: 공격 태그 및 스킬 발동 시마다 `VolumeHitbox(...)` 객체를 매번 새로 인스턴스화(`new`)함.
* **문제**: 초당 30 FPS로 동작하는 소형 임베디드 기기(RP2040/ESP32 MicroPython) 환경에서 잦은 메모리 할당은 주기적인 **GC(가비지 컬렉터) 멈춤 현상(Stuttering / Frame Drop)**을 유발함.
* **조치**: 플레이어 생성 시 히트박스 객체를 미리 재사용(Object Pooling 또는 Pre-allocated Instance)하도록 변경.

### 2) A+B 동시 입력 프레임 오차로 인한 필살기/무기 투척 씹힘 (Input Buffer)
* **대상**: `player.py` (`update` 메인 프레임)
* **현상**: `A+B` 버튼 동시 누름(필살기/무기 던지기) 판정 시, 사용자가 `B` 버튼을 1프레임이라도 먼저 누르면 `B` 버튼의 점프(`is_jumping = True`)가 먼저 발동하여 필살기가 씹힘.
* **문제**: 임베디드 패드 특성상 두 버튼이 정확히 동일 프레임에 눌리기 힘들어 필살기 조작감이 떨어짐.
* **조치**: 2~3프레임 분량의 **입력 버퍼(Input Buffer)**를 두어 `B` 입력 직후 `A`가 들어와도 필살기로 인정하도록 개선.

### 3) 히트박스 사거리 계산 오차 (`hitbox.py`)
* **대상**: `hitbox.py` (`check_overlap`)
* **현상**: `attack_x = self.owner.x + (direction * self.range_x)` 계산 후 `abs(attack_x - target.x) <= self.range_x`로 판정함.
* **문제**: `range_x`가 오프셋과 반지름 양쪽으로 중복 적용되어 실제 공격 사거리가 의도했던 `range_x`보다 2배 멀리까지 미치는 현상 발생.
* **조치**: 중심 오프셋과 실제 타격 박스 폭(Width)을 분리하여 직관적인 픽셀 영역 계산식으로 수정.

### 4) `main.py` 몬스터 순회 중 원거리 무기 몬스터 데미지 연속 중복 적용
* **대상**: `main.py` (Weapon Throw / Skill Command 루프)
* **현상**: 무기 던지기 및 스킬 발동 시 `for enemy in world_enemies:` 루프 안에서 사거리 내 모든 적에게 피격을 주지만, 프레임당 1회 타격 제한(Hit-ID 또는 Cooltime)이 없음.
* **조치**: 1회 공격 스킬당 적별 이미 타격 여부(`damaged_targets` set)를 체크하여 다중 피해 방지.
