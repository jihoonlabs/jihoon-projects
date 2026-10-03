# 개인 게임 AI — 게임 폴더 연결

갱신일: 2026-10-03
브랜치: feature/personal-game-ai-thumby

## 목표·규칙
- 지정 게임 폴더의 자동 수정·검사를 연결한다. 작업 자동 분할·파일 생성은 후속 범위다.
- 같은 My PRJ 폴더에서 AGENTS.md와 이 문서만 지침으로 사용한다.
- AGENTS.md 수정 금지. 수정본은 파일 전체로 제공한다.
- 기존 untracked 5개·stash 1개·runner_tasks.json을 보존한다.
- 추가 commit·push·merge는 별도 승인 후 진행한다.
- main 통합·브랜치 삭제는 하지 않는다.

## 연결 계약
- sandbox 동작 유지. game/파일.py는 target.json의 edit_directory 바로 아래로 연결한다.
- edit_directory는 저장소 내부 상대 경로이며, 미지정 시 게임 수정을 차단한다.
- 대상·고정 테스트는 Git 추적 상태이고 기존 변경이 없어야 한다.
- 경로 이탈·심볼릭 링크·실행 중 외부 변경을 차단한다.
- Docker는 선택 폴더만 읽기 전용으로 검사하고 기존 격리·자원 제한을 유지한다.
- 고정 테스트 보호·질문 시 원본 복원·답변 후 재개를 유지한다.

## 게임 관리
- 플랫폼 부모 → 게임 Epic → 작업 Child. 각 브랜치에 전용 MD 하나를 둔다.
- 플랫폼: feature/thumby / feature/thumby-color / feature/starcraft.
- 코드: micropython/thumby/<게임명>/ 또는 micropython/thumby-color/<게임명>/.
- 스타 경로는 추후 확정한다. AI 도구 개발은 게임 브랜치와 분리한다.

## 현재 상태
- 기준 commit: 284640f. 고정 게임 경로를 설정 방식으로 변경한 상태다.
- 게임 파일 두 개는 삭제 변경으로 분리했다. 이동 구현·테스트는 아래 백업에 보존했다.
- 백업: /var/folders/5x/_d4_99cx6w74qs7259bd07s80000gn/T/street-rpg-preserve-tgl_znvx
- feature/thumby는 main 8f0e79e에서 생성했다. 게임 Epic·Child는 아직 없다.
- 현재 설정에는 edit_directory가 없다. 게임 브랜치용 실행 환경은 미준비다.

## 검증·제한
- 회귀·연결·설정 테스트 75개와 staged·unstaged diff 검사 통과.
- 경로 고정 제거 전 실제 모델 구현·Docker 이동 테스트 8개 통과.
- 생성 코드의 끝 공백을 수동 정리한 뒤 로컬 테스트 8개 통과.
- 백업 내용 일치·기존 untracked·stash 보존 확인.
- 설정 방식의 실제 모델·Docker 실행과 게임 브랜치 실행·재개는 미검증.
- 화면·실기 동작은 미검증. 자동 성공 판정에 Git diff 검사는 포함되지 않는다.

## 다음 작업
- 최종 diff 확인 후 승인받아 도구 정리 commit.
- Thumby 부모 문서 → 게임 Epic → 이동 Child 구성.
- 백업 파일 배치 후 별도 AI 실행 환경으로 게임 Child 연결 검증.