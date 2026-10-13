# 폴더 정리 결과

Ollama 도구는 `ai/personal-game-ai/`에 유지하고, 세 일반 Thumby 게임 폴더를
`micropython/Thumby/` 아래로 이동했다. `micropython/ThumbyColor/`는 향후 컬러 게임용이다.
기기 배포 경로 `/Games/ThumbyGrowth/`는 그대로다.

게임 실행 코드와 저장 파일, 기존 고정 테스트 내용은 변경하지 않았다.
보조 도구의 맥 worktree 절대 경로를 저장소 기준으로 바꿨다.
브랜치 확인은 target.json의 expected_branch를 사용하므로 Epic 설정과 일치한다.
게임 Epic은 `epic/thumby-growth`, 도구 Epic은 `feature/personal-game-ai`다.

AI 도구 테스트 380개와 바닥 이동 테스트 17개가 통과했다.
기존 게임 테스트 43개 중 9개 실패는 이동 전에도 있었고 결과도 동일했다.
전체 게임 검증 통과나 실제 기기 플레이 완료를 의미하지 않는다.

Mac의 기존 My PRJ AI 폴더와 바깥 worktree에는 Git에서 제외된 실행 기록이 있다.
브랜치 전환 전 My PRJ의 미추적 AI 폴더를 백업하고, 전환 후 양쪽 outputs를 합친다.
서로 다른 동명 기록은 백업을 남기고 덮어쓰지 않는다. 가상환경은 새 위치에서 재생성한다.
이전 workflow는 경로/문맥 검증에 막힐 수 있으므로 자동으로 이어 실행하지 않는다.
기록 보존과 실행 위치 검증 전 바깥 worktree를 삭제하지 않는다.
