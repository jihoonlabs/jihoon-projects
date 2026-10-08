# 게임 요청 준비 Child

- 브랜치: feature/personal-game-ai-request-intake. 기반: 생성 연결 fda316a. commit·일반 push 허용, merge 금지.
- 목표: 자연어 게임 요청에서 필요한 설정만 확인하고 요청 파일을 자동 준비한다. 전체 제작 흐름 중 1단계다.
- 범위: 원문 보존, play/finish 누락 질문, 대화형 답변, 새 요청 파일 저장, 선택적 모델 설정 추출과 사용자 확인.
- 대상외: workflow 자동 시작, 새 게임 대상/허용 API 설정, 기기 배포, 기존 ThumbyDodge 변경. target.json·게임·기존 요청·승인 기록은 변경하지 않는다.
- 현재 프로필은 좌우 버튼 중심이다. 시대극 격투 게임 전체를 구현 가능하다고 선언하지 않는다.

## 계약과 구현

- prepare(brief, settings): settings는 play/finish, 누락 질문 또는 goal/requirements/area 요청 반환. 모델을 호출하지 않는다.
- extract_settings(brief, settings, model=...): 누락 키만 요청하며 원문의 연속된 1~400자 인용/null JSON을 검증한다. 명시 설정이 모두 있으면 모델 호출을 생략한다. 중복 키·다른 키·원문 밖 값·잘못된 응답은 거부한다.
- --interactive: 아이디어와 누락 설정 질문 후 outputs/request_<고유값>.json 자동 저장. --output은 새 파일만 생성한다. 기존 파일을 덮어쓰지 않는다.
- --infer는 --interactive와 함께만 사용한다. 기존 ask_ai.ask_model 연결이며 추출 결과는 사용자 y 확인 후 적용한다. 거절·잘못된 응답·호출 실패면 직접 질문한다.
- 원문 인용 검사는 의미 정확성이나 모든 조건의 완전성을 보장하지 않는다. 확인은 설정 채택이며 기존 설계·테스트 승인과 별개다.

## 검증·재개

- 요청 준비 테스트 18개, 기존 생성 브랜치 이름/설정을 유지한 분리 검증 checkout의 전체 테스트 306개 통과. 실제 CLI·요청 파일 로더 연결·최대 길이 UTF-8·파일 보존·자동 저장·가짜 모델 확인/거절/실패 흐름을 검사했다. loader 테스트는 게임 경로 선택만 임시 경로로 대체했다.
- 실제 Ollama·Docker·Thumby 실행은 미검증. 가짜 모델 검증을 실제 모델 품질 확인으로 취급하지 않는다.
- 시작 자료: AGENTS.md → 이 MD → REQUEST_INTAKE_MANUAL.md → request_intake.py/test_request_intake.py.
- 이 Child에서 workflow.py를 바로 실행하지 않는다. target.json은 기존 생성 브랜치/ThumbyDodge용이다. 새 게임 대상과 생성 작업 문맥을 정한 후 workflow 연결을 구현한다.
- 집에서 --interactive --infer로 원문 설정의 누락/오인식과 실패 후 직접 질문을 확인한다. 문제는 테스트로 고정한 뒤 수정한다. 승인 digest를 임의 수정하지 않는다.
