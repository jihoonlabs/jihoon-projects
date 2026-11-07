# 개인 게임 AI — 수정 중 예외 시 대상 복원

갱신일: 2026-11-07
브랜치: feature/personal-game-ai-edit-restore
기준: feature/personal-game-ai 6348e38

## 목표
- 수정 도중 예외(모델 길이 중단, 테스트 시간 초과 등)가 나도 대상 파일을 원래대로 돌려, 같은 대상을 다시 실행할 수 있게 한다.

## 범위
- edit_loop.run_edit에서 후보를 쓴 뒤 예외가 나면, 대상이 도구가 마지막에 쓴 후보와 같을 때만 원래 내용으로 되돌린다.
- 대상이 외부에서 바뀌었거나 다른 종류(심볼릭 링크 등)로 바뀌었으면 되돌리지 않고 cleanup_error로 남긴다.
- 예외 때도 result.json에 status failed, error, attempts를 기록하고 예외는 그대로 다시 던진다.
- create_loop의 기존 정리 방식과 맞춘다.
- 제외: 강제 종료(SIGKILL)·전원 차단, Ctrl+C(KeyboardInterrupt), 잠금 형식, create_loop 변경.

## 현재 상태
- 구현 완료, 독립 검증 대기.
- 확인: 전체 회귀 290개 통과(Mac 호스트 Python 3.9.6, 기존 285 + 신규 5).
- 확인: 복원 쓰기, 외부 변경 확인, 종류 확인, 기록, cleanup_error, 예외 재전달, 시도 횟수를 하나씩 되돌리면 테스트가 실패한다.
- Mac 실측(2026-11-07, gemma4:26b, Docker python:3.11-slim, 실제 도구 경로): 로컬 테스트 사본에서 고정 테스트가 40초 걸리게 해 30초 초과 예외를 냈다. 예외 뒤 대상은 원래 내용으로 돌아왔고 Git 변경·잠금·남은 컨테이너가 없었다. result.json에 오류와 시도 1회가 기록됐다.
- 참고: workflow의 --retry는 설계·테스트 생성 단계에만 쓰인다. 실행 단계에서 실패한 작업을 다시 돌리는 기능은 이 브랜치 범위가 아니다.
