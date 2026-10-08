# 게임 제작 요청 준비

## 한 명령으로 질문과 저장

```bash
cd ai/personal-game-ai
python request_intake.py --interactive
```

게임 아이디어 → 핵심 플레이 → 종료/재시작 조건을 답하면 요청 파일을 도구 옆 `outputs/request_<고유값>.json`에 자동 저장합니다. JSON 복사나 저장용 Python 코드는 필요 없습니다. `--brief`, `--play`, `--finish`로 제공한 항목은 다시 묻지 않습니다. `--output 새파일.json`으로 저장 위치를 지정할 수도 있습니다. 기존 파일은 덮어쓰지 않으며, 입력 중단·잘못된 답변·누락 설정일 때 요청 파일을 만들지 않습니다.

질문과 요청 파일 저장까지 구현했습니다. 자연어 설정 자동 추출과 workflow 자동 시작은 아직 없습니다. 현재 Child의 생성 대상 설정은 기존 ThumbyDodge용으로 유지합니다. 아래 수동 저장 예제는 선택 사항입니다.

Ollama 없이 요청을 준비하는 첫 도구를 추가했습니다. 시나리오·분위기는 자연어 원문으로 보존하고, 핵심 플레이와 종료/재시작 조건 중 설정하지 않은 항목만 질문합니다. 코드 구조는 묻지 않습니다.

```bash
cd ai/personal-game-ai
python request_intake.py --brief '시대극 느낌의 작은 회피 게임'
python request_intake.py --brief '시대극 느낌의 작은 회피 게임' --play '좌우 이동으로 장애물 피하기' --finish '충돌하면 종료하고 양쪽 버튼으로 재시작'
```

두 번째 명령에 --request-only를 추가하면 기존 workflow용 JSON만 출력합니다. 새 파일명으로 저장한 뒤 내용을 확인하고 기존 workflow에 전달할 수 있습니다. 기존 요청 파일에 덮어쓰지 마세요.

이 도구는 원문을 이해해 정보를 자동 추출하지 않습니다. 이미 정한 내용은 --play/--finish로 전달해야 합니다. 생성·모델 호출·파일 쓰기는 하지 않습니다. JSON 준비가 게임 구현 가능성을 보장하지 않습니다. 현재 좌우 버튼 프로필로 시대극 격투 게임 전체를 만들 수 있다고 검증한 상태도 아닙니다.

기존 게임 요청·승인 기록·target.json은 변경하지 않았습니다. 사용자가 원한 자연어 제작 툴의 입력 준비 단계이며 완성된 자동 제작 툴은 아닙니다.

요청 준비 테스트 13개와 기존 설정을 유지한 별도 검증 checkout의 전체 테스트 301개가 통과했습니다. 실제 명령행 실행으로 한글 JSON 출력, 누락 질문, workflow 요청 형식 및 잘못된 입력 8종의 오류 처리를 확인했습니다. 최대 길이 UTF-8 요청을 실제 workflow 파일 로더와 validator로 읽고 파일이 바뀌지 않는 것도 확인했습니다. 게임 경로 선택만 임시 경로로 대체했으므로 현재 Child에서 실제 생성 실행까지 검증한 것은 아닙니다. 오류일 때 stdout에 요청 JSON을 내보내지 않습니다. Ollama·Docker·실제 Thumby 생성은 실행하지 않았습니다.

요청 파일 저장 시 단순한 `> 기존파일`은 실행 실패 전에 기존 파일을 비울 수 있습니다. 아래 예시는 성공한 JSON만 새 파일에 저장하며 같은 이름이 있으면 중단합니다. 도구 폴더에서 실행하고 새 게임 아이디어와 설정으로 바꾸세요.

```python
import json
import subprocess
import sys
from pathlib import Path

result = subprocess.run([
    sys.executable, "request_intake.py", "--brief", "산길 회피 게임",
    "--play", "좌우 이동으로 장애물 피하기",
    "--finish", "충돌하면 종료하고 양쪽 버튼으로 재시작",
    "--request-only",
], check=True, capture_output=True, text=True, encoding="utf-8")
json.loads(result.stdout)
with Path("new-game-request.json").open("x", encoding="utf-8") as stream:
    stream.write(result.stdout)
```

`--request-only` 없는 출력은 질문·상태 정보이며 workflow 요청 파일로 사용할 수 없습니다. 준비된 새 요청도 현재 ThumbyDodge workflow 기록에 전달하지 말고, 새 게임 경로와 브랜치 설정을 먼저 확정하세요.

집에서 먼저 `python -m unittest test_request_intake -v`를 실행하세요. 다음 개발은 자연어에서 설정을 추출하는 모델 연결입니다. 출력 계약과 원문 근거 검사부터 정하고, 가짜 모델 응답 테스트 후 실제 Ollama로 검증해야 합니다. 키워드만 보고 사용자의 조작·종료 조건을 임의 확정하지 마세요. 현재는 `--play`와 `--finish`를 직접 제공하는 방식입니다.

집의 Ollama에는 AGENTS.md, REQUEST_INTAKE.md, 이 MANUAL을 먼저 읽게 한 뒤 작업 코드와 테스트를 확인하도록 하면 됩니다. 이 브랜치는 입력 준비용이며 현재 target.json은 기존 Thumby 생성 브랜치를 가리키므로 여기서 workflow.py를 바로 실행하지 마세요. 새 게임의 경로·조작 범위를 확인한 후 생성 작업에 요청을 전달하는 단계가 남아 있습니다. merge는 하지 않았습니다.
