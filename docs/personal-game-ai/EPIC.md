# 개인 게임 AI — Epic

갱신일: 2026-11-07
브랜치: feature/personal-game-ai

## Router
- Thumby 대상 검사 — feature/personal-game-ai-thumby-platform — Epic 통합 완료(2026-11-07). 상세: personal-game-ai-thumby-platform.md
- Gemma 응답 처리 — feature/personal-game-ai-gemma-json — Epic 통합 완료(2026-11-07). 상세: personal-game-ai-gemma-json.md
- 수정 중 예외 시 대상 복원 — feature/personal-game-ai-edit-restore — Epic 통합 완료(2026-11-07). 상세: personal-game-ai-edit-restore.md

## 목표·규칙
- 로컬 Ollama로 게임 개발을 진행하고 사용자는 목표와 중요한 분기를 결정한다.
- 목표→설계→계획→파일 생성·수정→검사→재개를 연결한다.
- 외부 유료 API는 사용하지 않는다.
- main → Epic → Child. 검증 후 바로 위 부모에 통합한다.
- Child는 별도 브랜치·worktree를 사용할 수 있다.
- 코드: ai/personal-game-ai/. 문서: docs/personal-game-ai/.
- 지침은 AGENTS.md와 현재 브랜치 MD 하나만 사용한다.
- AGENTS.md 수정 금지. 개인 AI 문서는 한국어로 제공한다.
- 기존 untracked·stash·runner_tasks.json을 보존한다.
- commit·merge는 승인 범위 안에서 수행한다. 공개 push는 사용자 승인 시에만 진행한다.
- main 통합·완료 Child 삭제는 하지 않는다.
- 게임 그래픽 작업은 중단하고 자동화 도구 개발을 우선한다.
- 사용자는 핵심 디자인·시나리오·규칙을 선택하고 명세를 승인한다.
- 원본 복사는 절대 금지한다. 독자적인 코드·캐릭터·어셋·시나리오·데이터를 제작한다.
- 제품 목표: [GOAL_V1](https://github.com/jihoonlabs/jihoon-projects/blob/4652b866e0163db14fb8ef54778417be19f9e075/docs/personal-game-ai/GOAL_V1.md). 플랫폼 작업: [썸비 Epic](https://github.com/jihoonlabs/jihoon-projects/blob/4652b866e0163db14fb8ef54778417be19f9e075/docs/thumby/EPIC.md).

## 파일 실행
- edit: 기존 Python 파일 수정. create: 없는 Python 파일 하나 생성.
- 문법·고정 Docker 검사와 최대 3회 재수정을 지원한다.
- 실행 잠금·외부 변경 검사·고정 테스트 보호를 적용한다.
- Docker는 네트워크 차단·읽기 전용 마운트·자원 제한을 사용한다.
- edit는 대상·테스트의 Git 추적과 기존 변경 없는 상태를 요구한다.
- create는 대상 부재와 고정 테스트의 Git 추적·변경 없는 상태를 요구한다.
- 외부 변경은 보존하고 중단한다. 후보·로그는 outputs에 남긴다.
- sandbox 또는 설정의 edit_directory 바로 아래 파일만 취급한다. 경로 이탈·심볼릭 링크를 차단한다.

## 계획·설계·테스트
- 목표와 사람이 지정한 대상·작업 종류·고정 테스트로 계획을 생성한다. edit/create만 허용한다.
- depends_on의 없는 ID·중복·자기 참조·순환을 차단하고 선행 작업부터 실행한다.
- 선행 작업이 tests_passed일 때 검증된 코드를 후속 요청에 전달한다. 요청 4000자 제한을 유지한다.
- 목표·필수 조건·허용 영역에서 파일 구성·함수 계약·검사 사례를 제안한다.
- 검토 의견과 이전 설계를 모델에 전달해 새 설계를 생성한다.
- SHA-256과 생성 당시 문맥을 확인해 승인 기록을 생성한다.
- 승인한 설계로 unittest 후보를 생성하고, 검토 후 확정한다. 후보는 실행하지 않는다.
- 확정 테스트를 덮어쓰기 없이 설치하고 create 계획을 생성한다. Git 자동 commit은 하지 않는다.

## 단일 실행 워크플로
- 요청 JSON 하나로 설계·테스트 후보·설치·구현 계획·실행을 연결한다.
- 설계 승인·테스트 확정은 SHA-256 검토 후 별도 입력한다.
- 설계·테스트 생성 실패는 명시적 --retry로 재시도한다.
- --test-feedback으로 테스트 후보를 다시 생성한다. --review-design으로 수정 설계를 연결한다.
- --recover는 검사 후 running 작업을 pending으로 되돌리고 실행을 이어간다. 검사 조건을 만족하지 않으면 거부한다.

## Thumby 대상 검사
- target.json의 선택 설정 platform: "thumby"는 edit_directory가 있을 때만 유효하다.
- 설정 시 run_test는 정적 검사 실패를 Docker 없이 피드백으로 돌려주고, 통과하면 가짜 thumby 모듈을 읽기 전용으로 붙여 검사한다.
- 설정 시에만 수정·생성 요청에 Thumby 제약 안내를 덧붙인다.

## Gemma 응답 처리
- 모든 모델 요청에 think:false를 넣는다.
- 수정·생성·설계·계획 응답은 응답 전체를 감싼 ``` 또는 ```json 울타리 하나를 벗기고 JSON으로 읽는다. 다른 형태는 형식 오류로 돌려준다.
- 원본 응답은 그대로 저장한다.

## 수정 중 예외 시 대상 복원
- 후보를 쓴 뒤 예외가 나면 대상이 도구가 쓴 후보 그대로일 때만 원래대로 되돌린다. 외부 수정·교체된 대상은 두고 cleanup_error로 남긴다.
- 예외 때도 result.json에 failed·오류·시도 횟수를 기록한다.

## 제한
- 모델: gemma4:26b. Docker: python:3.11-slim.
- 테스트 통과는 지정 범위만 보장한다. 구조 검사만으로 의미상 정확성이나 검사 충분성을 보장하지 않는다.
- SIGKILL 후 실행 잠금 파일이 남는다. 실행 중인 프로세스가 없음을 확인한 뒤 잠금 파일을 수동으로 삭제해야 한다.
- 복구 거부 시 traceback을 출력한다.
- create 대상이 일부 기록된 채 남으면 정리 전까지 복구를 거부한다.
- 생각을 끄면 추론 품질이 떨어질 수 있다. 실측 설계의 기대값 두 개가 스스로 정한 정렬 규칙과 맞지 않았으므로 설계 승인 단계에서 걸러야 한다.
- 가짜 thumby 모듈은 글자 모양·속도·메모리를 재현하지 않는다. 정적 검사는 MicroPython 컴파일이 아닌 휴리스틱이다.
- 수정 중 예외 복원은 SIGKILL·전원 차단·Ctrl+C를 다루지 않는다. 예외 없이 3회 실패하면 마지막 후보가 남는다.
- 실행 단계 실패 작업의 재실행 명령은 없다(--retry는 설계·테스트 생성 전용).
- 미검증: 실제 질문·답변 재개, 장시간 무인 실행, 실기·에뮬레이터 실행, 생성·계획 흐름의 실제 모델 실행.

## 다음 작업
- 실제 모델의 질문·답변 후 재개를 검증한다.
- 다음 우선 작업은 일반 Thumby의 작은 게임 생성·실행과 플레이 의견에 따른 수정이다.
