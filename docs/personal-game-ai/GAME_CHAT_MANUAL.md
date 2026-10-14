# Ollama로 썸비 작업 이어가기

현재 게임은 `epic/thumby-growth`의 ThumbyGrowth다. 집의 Ollama와 외부 AI가 같은 Git/WORK를 이어받는다.
`이어서 해` 또는 `/continue`는 조회가 아니라 WORK의 합의된 작업 하나를 구현하는 입구다.

## 실행

현재 브랜치와 로컬 변경을 확인하고 검증된 원격 변경을 받은 뒤 실행한다. 기존 미커밋 변경을 덮어쓰지 않는다.

```bash
cd "/Users/parkjihoon/workspace/My PRJ/ai/personal-game-ai"
source .venv/bin/activate
export GAME_AI_NUM_CTX=32768
export GAME_AI_NUM_PREDICT=16384
python3 game_chat.py
```

Ollama와 qwen3-coder:30b, 실행 중인 Docker 및 이미 준비된 python:3.11-slim 이미지가 필요하다.
외부 유료 모델 API는 사용하지 않는다. Docker 이미지는 실행기가 자동 다운로드하지 않는다.

continue는 private 규칙의 최신 main을 읽는다. 기본 탐색 위치는 게임 저장소의 형제 폴더
`jihoon-ai-internal/AGENTS_INTERNAL.md`다. 다른 위치면 실제 파일을 확인한 뒤 아래 환경변수로 지정한다.

```bash
export GAME_AI_INTERNAL_RULES="/실제/private-checkout/AGENTS_INTERNAL.md"
```

private checkout의 origin이 jihoonlabs/jihoon-ai-internal인지 검증하고 main을 fetch한 후 origin/main의 원문을 읽는다.
권한/네트워크/실제 경로가 없으면 이유를 출력하고 차단한다. public 규칙으로 몰래 대체하지 않는다.
Git commit을 위한 사용자 정보와 origin push 권한도 실제 Mac에서 필요하다.

## 작업 흐름

1. 현재 branch/WORK/Git 상태/최신 내부 규칙을 확인한다.
2. WORK와 실제 코드의 합의된 미완료 작업 하나를 선택한다. 중요한 미결정만 질문한다.
3. rules.py, ThumbyGrowth.py, scene_art.py 중 필요한 최대 3파일을 수정한다.
4. 기존 전체 게임 검사가 수정 전에 통과해야 한다. 기존 검사는 모델이 변경하지 않는다.
5. 후보를 API/문법 검사하고, 작업 전용 unittest와 전체 게임 검사를 격리된 Docker에서 실행한다.
6. 실패 피드백으로 최대 3후보를 재시도한다. 20분 예산이며 모델 HTTP 요청은 남은 예산 안에서 제한한다.
7. 통과하면 WORK 결과를 갱신하고, target.json의 resume_publish=true일 때 소유한 변경만 commit/push한다.

Docker는 네트워크 차단·읽기 전용 마운트·권한/자원 제한을 유지한다. 호스트에서 생성 코드를 실행하지 않는다.
전체 회귀와 모델이 만든 작업 검사의 통과가 실기 성능이나 그림의 아름다움을 증명하지는 않는다.
모델의 판단력을 기존 검사만으로 보장하지 않는다. 실제 결과와 변경 내용을 함께 확인한다.

실패 후보는 원본으로 복원하며 외부 편집은 보존한다. 기존 dirty/staged 변경, Git 기준 변경, 검사 변경은 차단한다.
commit/push 실패 시 검증된 코드·WORK·생성 검사는 보존한다. Git 상태와 로그를 보고 같은 변경의 publication부터 마무리한다.
merge, branch 삭제, 새 게임 자동 생성, 임의 셸 작업은 실행하지 않는다.

## 명령과 출력

- `이어서 해`, `썸비 이어서 해`, `/continue`: WORK 기반 한 작업
- `/status`: 실제 브랜치/모델/게임 변경 확인
- `/read rules.py`, `/read ThumbyGrowth.py`: 명시적 전체 코드 조회
- `/test`: 기존 test_floor_movement 검사. continue의 전체 검사와 다르다.
- 구체적인 단일 파일 수정 요청: 기존 수정 엔진 사용. 이 경로는 고정 검사/미커밋 결과 유지.
- `/cancel`: 대기 질문 취소
- `/exit`: 종료

일반 작업 출력은 진행/결과 요약이다. 전체 코드 출력은 명시적 조회에서만 사용한다.
질문 답변은 원래 작업과 연결해 재개한다. 질문 대기는 현재 프로세스에서 유지된다.

## 기록과 검증 수준

outputs/chat_<ID>/turns.jsonl에 요청/계획/모델 응답/실제 결과를 남긴다.
resume_baseline.txt와 resume_test_<시도>.txt는 Docker 검사 로그다.
resume_journal.json은 적용 전 원본/후보/작업 검사/기준 SHA를 기록한다. private 규칙 원문은 기록하지 않는다.
프로세스 강제 종료 시 잠금과 journal이 남을 수 있다. 자동 강제복구하지 않으며 실제 Git/파일 상태를 대조한다.

continue 모의 모델/검사 검증 13개: WORK 재개, 실패 재시도, 여러 파일 복원, 외부 편집 보호,
기존 검사 보존, dirty/규칙 부재/시간 상한 차단, 질문 재개, 소유 파일 commit/push 연결, publication 실패 보존.
실제 Mac Ollama 모델·Docker 연결·기기 플레이는 별도 검증이다. 모의 성공을 실제 모델 성공으로 주장하지 않는다.
