# 개인 게임 AI — 일반 Thumby 자동 제작 연결

## 목표
요청에서 작은 일반 Thumby 게임을 생성·검사하고 사용자가 플레이테스트할 수 있는 제작 흐름을 연결한다.

## 범위·규칙
- 브랜치: feature/personal-game-ai-thumby-generation
- 지침은 AGENTS.md와 이 문서만 사용한다. AGENTS.md는 수정하지 않는다.
- 최신 AI Epic에서 시작하며 기존 Thumby 브랜치·게임·미커밋 파일·stash를 보존한다.
- 도구 개발과 플랫폼→게임 Epic→게임 Child를 분리하는 기존 계약을 유지한다.
- 첫 검증 게임은 좌우 이동·장애물 충돌·점수·재시작이 있는 작은 게임이다.
- 게임 규칙과 일반 Thumby 입력·표시 코드를 분리한다.
- 실제 게임 경로와 브랜치는 기존 플랫폼 상태를 확인한 후 확정한다.
- 일반 Thumby 공식 API를 확인한다. Color와 StarCraft는 후속 범위다.
- 기존 설계·테스트 검토와 SHA-256·Git 보호·Docker 검사를 유지한다.
- 회사에서는 GitHub 코드 작업, 집에서는 Ollama·Docker·기기 검증을 수행한다.
- 원격 변경은 이 Child의 작업 범위로 제한한다. main·포트폴리오 통합과 브랜치 삭제는 수행하지 않는다.

## 현재 상태·계약
- 기준 Epic: 31a90f2. 전체 회귀 216개는 집의 이전 통합 검사에서 통과했다.
- workflow.py는 요청→설계→테스트 후보→설치→계획→구현을 연결한다.
- 승인·확정·테스트 Git 준비에서 멈추고 같은 요청으로 재개한다.
- game 영역은 설정의 edit_directory 바로 아래 파일을 취급한다.
- 게임 실행은 도구의 Git 제외 복사본과 게임 Child 설정을 사용하는 기존 계약이 있다.
- Child 설정의 expected_branch와 branch_document를 현재 브랜치·이 문서에 맞췄다.
- 분리된 임시 Git 검사 환경에서 read_context.py의 브랜치·경로·문맥 검사 통과(2417자)를 확인했다. 실제 Mac 전체 회귀를 실행한 것은 아니다.
- 생성 프로필을 통해 일반 Thumby 설계·테스트·구현 프롬프트 계약을 연결했다. 게임 규칙은 순수 Python으로, 기기 어댑터만 thumby API를 사용하도록 분리하고 CPython 테스트에서는 기기 의존성을 mock하도록 요구한다.
- 생성 코드 단계에서 Thumby Color import, 확인하지 않은 일반 Thumby API, 모듈 최상위 무한 루프를 차단하고 기존 재시도 루프로 수정하게 한다. 이 검사는 game+thumby 프로필에만 적용해 sandbox와 다른 프로필에는 영향을 주지 않는다.\n- 실제 게임 저장소의 edit_directory가 아직 확정되지 않아 새 게임 파일 생성 실행은 미검증이다.
- 이전 워크플로 기록은 문맥 변경 전 이력으로 보존한다.

## 검증·제한
- 이동 경계·충돌·점수·재시작을 자동 검사한다.
- CPython 검사는 MicroPython 호환성과 실제 기기 화면·속도를 보장하지 않는다.
- 실제 Ollama·Docker·기기 검증과 모의 검사를 구분해 기록한다.
- GitHub 연결만으로 집의 Ollama가 원격 실행되지는 않는다.

## 공식 API 확인
- 출처: https://thumby.us/API/Get-Started/ 및 https://thumby.us/API/Link/
- 일반 Thumby는 import thumby를 사용한다.
- 좌우 입력: thumby.buttonL.pressed(), thumby.buttonR.pressed().
- 표시: display.fill, drawFilledRectangle, drawText, update. 속도 설정은 display.setFPS.
- 기기 실행 어댑터는 무한 루프를 import 시 실행하지 않도록 검사 가능한 함수와 실제 진입을 구분한다.

## 집에서 바로 검증
1. Child 최신 원격을 반영한 뒤 `ai/personal-game-ai`에서 생성 프로필 단위 테스트를 실행한다.
   - `python -m unittest test_generation_profile -v`
   - 생성 프로필 테스트가 모두 통과해야 다음 단계로 진행한다.
2. 프로젝트의 기존 전체 회귀 명령으로 회귀 검사를 실행한다.
   - 기존 기준은 216개 통과다. 현재 Child 변경 때문에 실패하면 먼저 원인을 수정하고 재검사한다.
3. 실제 Ollama로 첫 게임 요청을 실행한다.
   - 요구사항: 좌우 이동, 장애물 충돌, 점수, 재시작.
   - 설계 결과에서 순수 Python 게임 규칙과 일반 Thumby 어댑터가 분리됐는지 확인한다.
   - 테스트 후보가 실제 thumby 없이 CPython/Docker에서 검사 가능한 구조인지 확인한다.
4. 실제 게임 파일 생성 직전에는 중단한다.
   - `edit_directory`와 플랫폼 기준 브랜치를 확인하기 전에는 게임 저장 경로를 추측하지 않는다.
   - 기존 `micropython/ThumbyFight`를 수정하거나 덮어쓰지 않는다.

### 합격 기준
- 생성 프로필 단위 테스트 통과.
- 기존 전체 회귀 통과.
- Ollama 설계가 rules/device 경계를 지킨다.
- 생성 테스트가 이동 경계·충돌·점수·재시작을 직접 검증한다.
- 일반 Thumby API만 사용하고 Thumby Color 또는 추측 API가 없다.
- 위 조건을 만족한 뒤에만 실제 게임 경로·브랜치를 확정한다.

## 다음 작업
- 집에서 생성 프로필 단위 테스트와 전체 회귀를 실행하고, 실제 Ollama로 첫 게임의 설계·테스트 후보가 분리 계약을 따르는지 확인한다.
- 원격에 feature/thumby는 확인되지 않았다. 기존 플랫폼 분리 계약을 바꾸거나 새 게임 브랜치를 생성하기 전에 실제 기준을 확정한다.
