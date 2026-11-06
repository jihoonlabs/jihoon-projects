# 개인 게임 AI — Thumby 대상 검사

갱신일: 2026-11-06
브랜치: feature/personal-game-ai-thumby-platform
기준: feature/personal-game-ai f066064

## 목표
- 로컬 모델이 생성한 게임 코드를 원래 Thumby(72×40 흑백, MicroPython) 조건으로 자동 검사한다.
- 게임 코드·그림은 만들지 않는다. 모델이 받을 검사·피드백만 추가한다.

## 범위
- 검사용 가짜 thumby 모듈: 화면·스프라이트(VLSB)·버튼·소리·저장·링크와 테스트용 thumby.sim.
- MicroPython 호환 정적 검사: 문법, 허용 import·같은 폴더 모듈, 미지원 문법. 생성 코드는 실행하지 않는다.
- target.json의 선택 설정 platform: "thumby". edit_directory가 있을 때만 유효하다.
- 설정 시 run_test는 정적 검사 실패를 Docker 없이 피드백으로 돌려주고, 통과하면 가짜 모듈을 읽기 전용으로 붙여 검사한다.
- 설정 시에만 수정·생성 요청에 Thumby 제약 안내를 덧붙인다.
- 제외: 게임 코드, 실기·에뮬레이터 실행, 그레이스케일, Thumby Color, 한 요청에서 게임 전체 분할.

## 완료 기준
- platform 미설정 시 기존 동작과 회귀 테스트 유지.
- 가짜 모듈·정적 검사·run_test·설정·요청 안내 테스트 추가.
- 다른 모델의 독립 검증 통과 후 부모 브랜치 통합.
- 실제 모델·Docker 확인은 Mac에서 별도로 기록한다.

## 현재 상태
- 구현 완료, 독립 검증 대기. 아직 commit하지 않았다.
- 구현: platforms/thumby/thumby.py, platform_check.py, edit_loop.py·create_loop.py 연결, test_platform_check.py.
- 확인: 전체 회귀 276개(기존 243 + 신규 33) 통과, git diff --check 통과.
- 확인: 가짜 모듈을 PYTHONPATH로 붙인 CPython에서 버튼·화면 기록 예제 테스트 통과(Docker 명령과 같은 방식, Docker 자체는 아님).
- 미검증: 실제 Docker 실행(이 작업 공간에 Docker 데몬 없음), 실제 모델 생성, MicroPython 실기·에뮬레이터.
- 한계: 가짜 모듈은 글자 모양·속도·메모리를 재현하지 않는다. 정적 검사는 MicroPython 컴파일이 아니다.
