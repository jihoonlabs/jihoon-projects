# 게임 요청 준비 Child

- 브랜치: feature/personal-game-ai-request-intake
- 기반: Thumby 생성 연결의 원격 fda316a와 동일한 코드 tree. 기존 작업 폴더·집 산출물은 변경하지 않는다.
- 목표: 게임 제작 툴의 입력 준비. 자연어 원문을 보존하고 이미 제공한 사용자 설정을 다시 묻지 않는다.
- 범위: Ollama 없이 핵심 플레이와 성공/실패/재시작 조건의 누락 질문, 기존 workflow 요청 JSON 생성.
- 대상외: 자연어 의미 자동 추론, 설정 추천 모델, 생성 자동 실행, 기기 배포, 기존 ThumbyDodge 변경.
- 계약: request_intake.prepare(brief, settings); settings는 play/finish. request_ready이면 goal/requirements/area 형식 출력. 승인·설계·테스트 보호는 기존 workflow가 담당한다.
- 현재 프로필은 좌우 버튼 중심이다. 시대극 액션을 지금 구현 가능하다고 선언하지 않는다. 새로운 조작/API/게임 경로 설정은 설계 전에 별도 확인한다.
- 커밋·Child push는 사용자 승인 범위, merge는 하지 않는다. target.json과 기존 THUMBY_GENERATION.md를 변경하지 않는다.
- 자연어 원문만으로 이미 결정된 정보를 추출하는 단계는 아직 없다. 현재 구현은 명시한 설정을 기준으로 질문을 생략하는 첫 단계다.

## 성과·검증·재개

- 변경: ai/personal-game-ai/request_intake.py, test_request_intake.py, 이 작업 MD와 MANUAL. 기존 게임·요청·승인 기록·target.json은 수정하지 않았다.
- 기능 단위 테스트 5개 통과. Thumby 생성 브랜치 이름과 기존 설정을 유지한 분리 검증 checkout에서 전체 unittest 293개 통과. 새 Child에서 기존 read_context가 통과했다고 주장하지 않는다.
- 로컬/Ollama 재개 시작 자료: AGENTS.md → 이 MD → REQUEST_INTAKE_MANUAL.md → request_intake.py/test_request_intake.py.
- 이 Child는 입력 준비만 담당한다. target.json의 expected_branch와 branch_document는 기존 Thumby 생성 작업용으로 유지했다. 이 Child에서 workflow.py를 바로 실행하지 않는다.
- 로컬 명령: ai/personal-game-ai에서 python -m unittest test_request_intake -v; python request_intake.py --brief '게임 아이디어'; --play와 --finish로 이미 결정한 내용을 전달한다.
- --request-only 출력은 기존 goal/requirements/area 계약과 구조적으로 호환된다. 실제 설계·생성에 전달하기 전 사용자 설정 및 새 게임 폴더/허용 API 범위를 확인한다. 기존 ThumbyDodge 요청 파일이나 진행 중 workflow 문맥을 덮어쓰지 않는다.
- 미검증: 실제 Ollama를 통한 설계/생성, Docker 게임 검사, 기기 실행. 모델 호출 없이 준비 기능과 요청 validator 연결을 검사했다.
- 다음 책임: 자연어에서 이미 결정된 항목을 추출하고 필요한 질문만 제안하는 모델 연결. 지금의 두 설정 질문을 모든 장르에 충분한 자동 설계라고 취급하지 않는다. 기존 설계·테스트 승인 경계를 자동 통과시키지 않는다.
