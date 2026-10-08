# 게임 제작 요청 준비

전체 제작 흐름 중 1단계인 요청 준비 도구입니다. 한 명령에서 아이디어와 빠진 설정을 받아 JSON 복사 없이 요청 파일을 저장합니다.

```bash
cd ai/personal-game-ai
python request_intake.py --interactive
```

이미 결정한 항목은 --brief/--play/--finish로 전달하면 다시 묻지 않습니다. 기본 저장 위치는 도구 옆 outputs/request_<고유값>.json이며 --output 새파일.json으로 지정할 수도 있습니다. 기존 파일은 덮어쓰지 않습니다. 입력 중단·잘못된 답변·누락 설정일 때 요청 파일을 만들지 않습니다.

## 집에서 모델 설정 추출 확인

```bash
python -m unittest test_request_intake -v
python request_intake.py --interactive --infer --brief '좌우 이동으로 장애물을 피하고 충돌하면 종료, 양쪽 버튼으로 재시작하는 산길 게임'
```

--infer를 붙이면 기존 Ollama 연결로 원문에서 play/finish 설정을 찾습니다. 추출 결과를 보여주고 y로 확인한 항목만 적용합니다. 거절하거나 추출에 실패하면 직접 질문으로 이어갑니다. Ollama 없이 쓰려면 --infer를 빼면 됩니다. 두 설정을 모두 직접 제공했다면 모델을 호출하지 않습니다.

원문 밖의 제안·잘못된 JSON·중복 키는 거부하지만, 원문 인용 자체가 의미를 정확하게 분류했다고 보장하지는 않습니다. 예시 원문이 올바르게 분류되는지 실제 Ollama로 확인해야 합니다. 이번 원격 작업에서는 실제 모델을 실행하지 않았습니다.

요청 준비 테스트 18개와 기존 설정을 유지한 별도 checkout의 전체 테스트 306개가 통과했습니다. 가짜 모델로 채택·거절·잘못된 제안·호출 실패부터 저장까지 검사했습니다. 기존 CLI, 최대 길이 UTF-8 파일 로더 연결, 기존 파일 보존도 검사했습니다.

자동 저장은 구현됐지만 workflow 자동 시작·게임 생성·기기 전달은 아직 연결되지 않았습니다. 현재 target.json은 기존 Thumby 생성 브랜치/ThumbyDodge용입니다. 이 Child에서 workflow.py를 바로 실행하거나 새 요청을 집의 기존 workflow 기록에 덮어쓰지 마세요. 새 게임 경로와 허용 API 범위를 먼저 정해야 합니다. 실제 Ollama·Docker·기기 실행은 미검증이고 merge는 하지 않았습니다.

집의 작업 AI는 AGENTS.md, REQUEST_INTAKE.md, 이 MANUAL부터 읽고 코드·테스트를 확인하면 됩니다. 다음 개발 책임은 새 게임 대상 설정과 기존 설계·고정 테스트·구현 workflow 연결입니다. 사용자 설정 확인을 기존 설계·테스트 승인 대신 사용하지 않습니다.
