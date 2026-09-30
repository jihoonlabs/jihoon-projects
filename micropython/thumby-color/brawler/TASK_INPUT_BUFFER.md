# Task Specification: Input Buffer & Hitbox Fix (TASK_INPUT_BUFFER.md)

## 📌 목표 (Objectives)
1. **`A+B` 필살기/무기 던지기 입력 버퍼(Input Buffer) 구현**:
   - `B` 버튼(점프) 입력 후 3프레임 이내에 `A` 버튼이 눌려도 점프가 씹히고 `A+B` 필살기/무기 던지기가 정상 발동하도록 입력 버퍼 작성.
2. **`hitbox.py` 오프셋 사거리 공식 정밀화**:
   - `attack_x` 오프셋과 `range_x` 중복 적용 오차 수정.
3. **히트박스 객체 재사용 (MicroPython GC 최적화)**:
   - `Player` 클래스 내에 콤보 1, 2, 3단계 및 필살기용 `VolumeHitbox` 사전 할당(Pre-allocated) 참조 객체 적용.

---

## 🛠️ 작업 파일
- `micropython/thumby-color/brawler/engine/player.py`
- `micropython/thumby-color/brawler/engine/hitbox.py`
