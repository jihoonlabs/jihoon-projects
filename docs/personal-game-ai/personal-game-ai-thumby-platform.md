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
- 구현 완료(8b41730), Mac 실측 완료, 독립 검증 대기.
- 구현: platforms/thumby/thumby.py, platform_check.py, edit_loop.py·create_loop.py 연결, test_platform_check.py.
- 확인: 전체 회귀 277개 통과(Mac 호스트 Python 3.9). 3.9는 match를 해석하지 못해 문법 오류로 거부하므로, match 거부 테스트를 상대 import 테스트와 나누고 호스트 버전에 맞춰 확인한다.
- Mac 실측(2026-11-07, gemma4:26b, Docker python:3.11-slim): 로컬 복제본의 9x5 커서 과제에서 가짜 모듈을 붙인 Docker 테스트 4개 통과.
  - 1회차 실행에서 모델이 없는 API draw_rectangle을 써서 가짜 모듈이 AttributeError로 돌려줬다.
  - 허용 밖 import가 있으면 Docker를 실행하지 않고 호환 검사 실패를 돌려준다.
- 실측 조건: 기본 설정의 gemma4:26b는 생각(thinking)에 출력 한도 4096을 모두 써서 응답이 길이 제한으로 중단됐다. 통과 실행은 측정용 스크립트에서 think:false와 ```json 울타리 제거를 적용했다. 공용 코드(ask_ai·edit_loop) 수정은 후속 작업으로 분리한다.
- 미검증: MicroPython 실기·에뮬레이터, 큰 게임 과제.
- 한계: 가짜 모듈은 글자 모양·속도·메모리를 재현하지 않는다. 정적 검사는 MicroPython 컴파일이 아니다.
