# ThumbyGrowth 첫 플레이용 게임

## 가장 큰 목적
실제로 플레이할 Thumby 게임 하나를 먼저 완성한다.
그 결과를 로컬 Ollama의 다음 게임 제작·수정에 사용할 검증된 기준으로 쌓는다.
집에서는 Ollama, 회사/외부에서는 ChatGPT 등 현재 가능한 작업자가 같은 Git 상태를 이어받는다.
Ollama 전담이나 도구 완성을 게임 완성의 선행 조건으로 삼지 않는다.

## 게임 범위
- 일반 흑백 Thumby 72×40. 소스는 `micropython/Thumby/ThumbyGrowth/`.
- 타이틀 A 새 게임 / B 저장 불러오기.
- 상하좌우 바닥 이동, 방향 공격, 일시정지, 패배 시 현재 전투 재도전.
- 5번의 전투, 점진적인 적 능력치와 마지막 보스.
- 전투 보상, 상점 구매, 장착/해제, 능력치 증가, 수동 저장/복원.
- 5회 승리 후 QUEST CLEAR. 엔딩에서 새 게임 또는 완료 상태 저장.
- 저장 포맷 version=1 유지. 새 게임 선택 자체는 저장을 덮어쓰지 않는다.

## 검증
- 이전 9개 실패는 바닥 이동 추가 후 남은 옛 계약의 테스트였다.
  상태 fixture에 y좌표, 입력 fixture에 U/D held를 명시했다.
  몸체 6×7, 월드 x=0..138, 몸체 끝 기준 플레이어 공격거리 8,
  적 공격거리 2, 이동이 막혀도 방향 전환하는 현재 계약으로 경계 검사를 수정했다.
  테스트를 삭제하거나 실패를 무시하지 않았으며 게임 코드를 구 계약으로 되돌리지 않았다.
- 게임 검사 51개 통과. 실제 버튼 입력에 해당하는 호출만으로
  5전투→구매→장착→저장/복원→보스→엔딩→새 게임을 확인했다.
- 표준 전체 게임 검사 명령:
  `python3 -m unittest discover -s micropython/Thumby/ThumbyGrowth -p 'test_*.py' -v`
- 실제 Ollama, Docker, MicroPython 기기/에뮬레이터 실행과 조작감은 별도 미검증.
- 이번 마무리는 ChatGPT 작성이다. Ollama가 생성·플레이했다고 주장하지 않는다.

## 배포
기기의 `/Games/ThumbyGrowth/`에는 `ThumbyGrowth.py`와 `rules.py` 두 파일을 넣는다.
상세 조작은 게임 폴더의 README.txt에 있다.

```bash
python3 micropython/Thumby/ThumbyGrowth/tools/package_game.py --output /tmp/ThumbyGrowth.zip
```

패키지에 도구·테스트·실행 기록·가상환경은 넣지 않는다.
BUILD.json은 두 실행 파일과 README의 SHA-256을 기록한다.
과거 설계 승인/테스트 SHA 기록은 수정하지 않는다. 현재 수정된 테스트에 예전 승인을 승계하지 않는다.

## 다음 작업
1. 집에서 기기/에뮬레이터에 올려 실제 조작·화면·저장·엔딩을 확인한다.
2. 문제를 재현 조건과 함께 고치고 같은 게임 검사를 통과시킨다.
3. 확인된 코드와 수정 전후·검사·플레이 기록을 Ollama 문맥/경험 검색에 재사용한다.
   기록 축적은 파인튜닝이나 자동 학습 완료와 다르다.
