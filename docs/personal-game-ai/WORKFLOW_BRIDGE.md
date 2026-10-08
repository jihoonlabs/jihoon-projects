# 생성 workflow 연결 Child

- 브랜치: feature/personal-game-ai-workflow-bridge. 기반: 요청 준비 원격 ddd0a6c. commit·일반 push 허용, merge 금지.
- 목표: 요청 준비 → 저장 → 별도 생성 checkout의 기존 workflow 호출. 제작 흐름 2단계의 연결 부분이며 전체 게임 생성 완료는 아니다.
- 범위: request_intake의 --workflow-dir, workflow_bridge 실행·설계 승인/테스트 확정 전달. 기존 target.json·생성 도구·게임·집 승인 기록을 수정하지 않는다.
- 시작: AGENTS.md → 이 MD → WORKFLOW_BRIDGE_MANUAL.md → workflow_bridge.py/request_intake.py/연결 테스트.

## 계약

- --interactive --workflow-dir <생성 도구 폴더>는 요청을 새 파일로 저장하고 그 파일 절대 경로를 기존 workflow.py --request에 넘긴다. 요청 파일 복사나 JSON 재작성은 하지 않는다.
- 생성 checkout은 사용자가 명시한다. 브랜치 자동 변경이나 target.json 교체를 하지 않는다. 실제 대상·허용 API·문서는 해당 생성 checkout에서 먼저 준비해야 한다.
- 검토 재개는 workflow_bridge.py --request <같은 파일> --tool-dir <같은 폴더>로 수행한다. --approve-design/--confirm-tests는 사용자가 확인한 digest를 그대로 전달한다. 자동 승인·digest 생성 없음.
- 기존 engine이 브랜치/문맥 검사, 잠금, 실행 상태, 승인·고정 테스트 보호를 담당한다. 연결기는 단계별 호출 결과를 반환하고 실패를 완료로 취급하지 않는다.
- --answer/--answer-text와 --retry를 연결기에서 전달한다. 답변 쌍·길이·동작 충돌은 호출 전에 검사하며 shell 없이 원문 인자로 넘긴다. 재시도는 명시 옵션에서만 수행하고 기존 engine의 중단 상태·잠금 검사를 유지한다. 질문 자동 대화 UI, 테스트 피드백·설계 수정 연결은 남아 있다.

## 검증과 재개

- 연결/입력 테스트 26개 통과. 기존 설정과 브랜치 이름을 유지한 별도 checkout에서 전체 319개 통과. 답변 전달·재시도 충돌 차단 및 실제 CLI→가짜 engine subprocess의 한글/개행/셸 문자 보존을 확인했다.
- 실제 workflow subprocess를 현재 Child에서 실행해 브랜치 불일치로 모델 호출 전 차단되고 요청 파일이 보존되는 것을 확인했다. 성공 단계 전달은 가짜 subprocess 응답으로 검증했다. 실제 Ollama/Docker 연결 성공은 미검증이다.
- iPhone a-Shell mini의 이전 check.pyz는 사용자 보고 PASS 5. 긴 로그 대신 짧은 결과를 전달하는 방식이 가능해졌다. 이번 bridge는 subprocess/Git/생성 checkout을 요구하므로 그 폰 검사와 별개다.
- 집에서는 기존 작업 폴더의 dirty/승인/산출물을 먼저 확인한다. 새 게임이면 기존 ThumbyDodge workflow에 그대로 시작하지 말고 새 대상 작업 설정을 준비한다. 새 요청/문맥은 기존 engine에서 별도 기록으로 분리된다.
