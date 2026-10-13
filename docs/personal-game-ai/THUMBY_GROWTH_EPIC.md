# ThumbyGrowth 게임 Epic

## 목표와 범위
일반 Thumby 72x40 흑백 액션 RPG를 로컬 Ollama로 개발한다.
가장 큰 목적은 Ollama로 실제 플레이 가능한 Thumby 게임을 만드는 것이다.
대화 실행 기능과 도구 개선은 이 게임 제작을 위한 수단으로 유지한다.
안정성과 효율화를 우선하며 게임 구현, 자동 검증, 실제 기기 플레이를 구분한다.
Ollama 도구 Epic `feature/personal-game-ai`와 게임 Epic을 구분한다.

## 작업 위치
- 브랜치: `epic/thumby-growth`
- 맥 checkout: `/Users/parkjihoon/workspace/My PRJ`
- 도구: `ai/personal-game-ai/`
- 게임: `micropython/Thumby/ThumbyGrowth/`
- 일반 Thumby 게임: `micropython/Thumby/<게임명>/`
- Color 게임: `micropython/ThumbyColor/<게임명>/` (현재 비어 있음)
- target.json의 expected_branch와 branch_document는 이 Epic을 가리킨다.
- 보조 도구는 저장소 상대 위치와 target.json의 브랜치를 사용한다.
- 기본 작업은 이 Epic에서 이어가며 새 checkout/worktree를 만들지 않는다.
- 원격 변경은 fetch 후 현재 상태를 확인해서 적용한다. 티켓 개발 브랜치와 게임 Epic을 서로 merge하지 않는다.

## 통합과 현재 상태
- Mac 미커밋 작업 보존: `8f5139e`.
- 폴더 정리 Child: `68626c5`를 fast-forward 통합했다.
- 게임 실행 코드와 기존 고정 테스트는 바이트 단위로 보존했다.
- 과거 outputs의 승인·설계·실행 기록은 변경하지 않는다.
- 경로, 브랜치, 문맥 변경으로 과거 승인/실행 기록의 자동 재개가 거부될 수 있다.
  새 문맥을 검토하고 필요하면 새 작업 기록을 만든다. SHA나 승인 기록을 임의로 고치지 않는다.
- Mac에만 있는 outputs/previous/.venv는 Git 업로드에 포함되지 않았다.
  My PRJ로 옮길 때 기존 양쪽 실행 기록을 보존하고 충돌 기록은 백업을 유지한다.
  .venv는 새 위치에서 다시 만든다. 보존 확인 전 바깥 worktree를 삭제하지 않는다.

## 검증과 다음 작업
- 경로 이동 전후 AI 도구 테스트 380개 통과.
- 바닥 이동 테스트 17개 통과.
- 기존 게임 전체 테스트 43개 중 9개 실패는 이동 전후 동일하다.
  이전 전투/화면 계약과 현재 바닥 이동 계약의 일치 여부를 검토해야 한다.
- 게임 보조 도구 10개의 도구 루트, 문법 검사, Git 공백 검사 통과.
- 이번 작업에서 Ollama 생성, Docker 실행, 기기 플레이는 수행하지 않았다.
- 다음 우선 작업: Mac checkout/실행 기록 통합, 기존 9개 실패의 계약 검토, 실기 확인.

## 대화 작업 입구
- `ai/personal-game-ai/game_chat.py`로 자연어 지시를 현재 게임 작업에 연결한다.
- 첫 범위: 상태/코드 확인, 고정 Docker 검사, 단일 실행 파일 수정과 모델 질문 답변.
- 기존 수정 엔진의 Git·문맥·경로·고정 테스트 검사를 유지한다.
- 실패 후보는 원본으로 복원하고 외부 편집은 보존한다. 실제 실행 결과를 기록한다.
- 사용 방법과 한계: `GAME_CHAT_MANUAL.md`.
- 모의 모델/검사 기반 대화 연결 검사 19개 통과. Mac Ollama·Docker 연결은 미검증이다.
- 대화 실행기 추가 후 AI 도구 전체 회귀 399개 통과. 실제 checkout의 `/status` 연결도 확인했다.
- 다음 우선 작업은 Mac 자연어 지시→실행 확인과 기존 게임 검사 계약 검토다.
  새 게임 설계→검토→생성의 기존 workflow 연결은 그 다음이며, 전체 자동 제작 완료로 취급하지 않는다.
