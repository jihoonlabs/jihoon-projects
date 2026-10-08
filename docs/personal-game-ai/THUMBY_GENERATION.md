# 개인 게임 AI — 일반 Thumby 자동 제작 연결

## 목적·범위
- 현재 Child: feature/personal-game-ai-thumby-generation
- 작은 일반 Thumby 게임의 자동 생성·검사 연결만 담당한다.
- 첫 검증 게임: `micropython/ThumbyDodge/`의 좌우 이동·장애물 충돌·점수·재시작 게임.
- 규칙은 순수 Python, 기기 입력·표시는 별도 어댑터로 나눈다.
- Color·StarCraft와 기존 게임 수정은 이번 범위 밖이다.

## 작업 기준
- AGENTS.md + 이 문서 + 필요한 코드/산출물로 재개한다.
- 시작 전 Git 상태·브랜치·설정·승인 대상을 확인한다.
- 확정 범위의 구현→검사→수정→재검사는 자율 진행한다.
- 새 설계·범위·구조 변경은 근거·추천·영향을 설명하고 승인받는다.
- 기존 변경·untracked·산출물·stash를 보존한다.
- MD는 현재 계약과 상태 중심으로 유지하며 경과를 append하지 않는다.
- 진행 중 인수인계는 이 작업 MD에 현재 상태로 유지하고, MANUAL은 완료/통합 시 사용자가 이유·결과·구현·검증·제약을 짧게 확인하는 보고로만 갱신한다.
- 로컬 workflow 실행 전/종료 후에는 이 MD를 최신화하되, 승인된 workflow 기록을 재개하는 도중에는 MD를 수정하지 않는다. MD를 바꾸면 context fingerprint가 달라져 기존 승인/실행 기록을 재사용하지 않는 것이 정상이며, 계약 변경이 필요할 때만 의도적으로 수정하고 새 workflow를 시작한다.
- AGENTS 변경과 MD 추적·전달 방식 변경은 별도 결정이다.
- 원격 작업은 이 Child 범위에 한정한다. main 통합·브랜치 삭제는 하지 않는다.
- 도구와 플랫폼→게임 Epic→게임 Child의 분리 계약을 유지한다.

## 실행 계약
- ai/personal-game-ai/target.json:
  - expected_branch: feature/personal-game-ai-thumby-generation
  - branch_document: docs/personal-game-ai/THUMBY_GENERATION.md
  - generation_profile: thumby
  - edit_directory: micropython/ThumbyDodge
  - code_files: [] (다른 기능 MD를 추가하지 않는다)
- 첫 요청 파일: ai/personal-game-ai/thumby_dodge_request.json.
- workflow.py: 요청→설계 검토→테스트 검토→설치→Git 준비→계획→구현.
- 승인·확정 SHA-256, 고정 테스트 Git 보호, Docker 검사 계약을 유지한다.
- generation_profile.py의 프롬프트 및 AST 검사는 game + thumby에서만 적용된다.
- 집의 Ollama·Docker·실제 기기는 원격 GitHub 연결만으로 실행되지 않는다.
- 기존 승인/실행 기록은 생성 당시 문맥에 묶여 있으므로 문서 변경 후 임의로 재사용하지 않는다.
- 같은 요청 경로라도 요청 내용·작업 문맥이 바뀌면 기존 기록은 보존하고 새 workflow 기록에서 설계부터 다시 시작한다. 동일 요청·문맥과 일치하는 기존 path-only 기록은 호환 재개한다.

## 강제 검사와 지침의 구분
- read_context.py는 실제 브랜치, 문서 경로, 문맥 분량과 지정 파일을 검사한다.
- generation_profile.validate_code 검사는 create_loop.py의 후보 저장 전 호출된다.
- AST 검사 범위: thumbyColor 이름 import, thumby 별칭/from import, 일부 직접 API 속성, 최상위 while True, 폴더명 엔트리의 MicroPython 런처 진입 guard.
- 모든 Color 모듈·간접 API 접근·import 중 루프 실행을 포괄적으로 차단하는 검사는 아니다.
- 순수 규칙/어댑터 분리는 현재 프롬프트 지침이며 전체 의미를 강제하는 gate는 아니다.
- 엔트리 고정 테스트는 CPython에서 fake `thumby`를 선주입하고, 실제 기기에서는 MicroPython 런타임 guard가 진입 함수를 호출하는 계약이다.
- 검사 통과가 MicroPython 호환성·게임 품질·실행 안전성을 보장하지 않는다.

## 현재 진단·검증
- 2026-10-08 원격 작업 환경 확인: Child HEAD는 `bca53184833a1d353e0c08a656be6087cc48c76c`, 시작 시 clean이었다. GitHub에서 `7370036`은 조회되지 않았다.
- 집의 미커밋 도구 수정·MANUAL·생성 코드·고정 테스트·outputs는 이 checkout에 없다. `micropython/ThumbyDodge/`에는 README만 있으므로 집 workflow의 `rules.py: tests_passed`, 어댑터 `pending`은 이 환경에서 재개·검증할 수 없다.
- 이 환경에서 요청 초과 시 전달용 계약 JSON 공백 축약과 AST가 동일한 선행 코드 재출력을 적용했다. 원본 task prompt·코드·artifact digest는 바꾸지 않으며, 축약 후에도 4000자를 넘으면 기존대로 거부한다. 집의 실제 요청 3988자는 자료 부재로 미확인이다.
- MicroPython 시작 guard의 else/elif에서도 진입 함수를 호출하는 후보를 거부한다. 정상적인 비시작 else는 허용한다. 직접 호출 AST 검사이며 간접 호출 전체를 증명하지 않는다.
- 도구 폴더 밖 게임 고정 테스트는 도구 기준 상대 경로로 기록하고, 검사 시 경로를 정규화해 지정 게임 폴더·파일 digest·Git 보호를 확인한다. 설치가 이미 중단된 집 기록의 자동 복구는 이번 변경에 포함하지 않았다.
- 테스트 후보의 각 메서드는 리터럴·리터럴 연산만 검사하는 assertion 외에 결과·상태 표현식을 받는 assertion이 필요하다. 함수 결과 변수·예외 검사는 허용하고 msg 키워드만 동적인 상수 비교는 인정하지 않는다. 이 AST 구조 검사는 대상 함수와 assertion의 데이터 흐름·도달 가능성·의미적 충족까지 증명하지 않으므로 후보 검토를 대체하지 않는다.
- 질문 답변 후 재개할 때도 계약 축약을 적용한다. 질문·답변을 붙이기 전에 prompt의 계약만 축약해 원문을 보존하며, 답변·선행 코드를 포함한 4000자 경계를 검사한다. 축약 가능한 초과 요청의 실패를 재현한 뒤 수정했다.
- 별도 임시 저장소의 실제 Git 명령으로 설치 경로/Git 보호 smoke 6항목 통과: 도구 폴더 밖 미추적 테스트, staged 테스트, clean commit된 테스트, 내용 변경, 추적 해제, 동일 내용 symlink. 원래 프로젝트에서는 commit하지 않았으며 이 확인에는 모델·Docker를 사용하지 않았다.
- 사용자 승인으로 읽기 전용 `review_workflow.py`를 추가했다. 명시한 workflow 기록의 요청·문맥·보호 산출물·고정 테스트 Git 상태·계획 계약·완료 artifact와 pending 요청 길이를 기존 검사로 확인한다. 모델·Docker·workflow 실행/승인/상태 수정은 하지 않는다. 잠금·불일치·실패·중단 단계는 blocked, 정상적인 읽기 검사는 reviewed로 보고한다. reviewed는 새 테스트 실행이나 기기 검증 완료를 의미하지 않는다.
- 로컬 재개 전 `python -B review_workflow.py --request thumby_dodge_request.json --record outputs/workflow_<실제ID>`를 실행한다. 기록은 자동 선택하지 않는다. exit 0은 읽기 검사 완료, exit 2는 차단 사유/기록 확인 필요다. 출력은 JSON이며 디스크 보고서를 자동 생성하지 않는다.
- 원격 환경 전체 unittest 286개 통과. 검토 도구 14개 테스트는 실제 임시 Git fixture로 정상/변경/잠금/문맥 불일치/잘못된 completed/초과 요청을 확인하고 기록 미변경·모델/Docker 미호출을 검사한다. 기존 테스트의 symlink 부모 디렉터리 누락과 프로필 지침 위치 assertion을 수정했다. Docker/Ollama/Codex CLI는 없으며, 모델 호출·Docker 검사·실기 플레이는 미검증이다. 이 대화의 코딩 지원과 workflow의 Ollama 모델 호출은 별개다.
- 다음 재개에는 집의 현재 `rules.py`, 고정 테스트 두 파일, 미커밋 도구 수정, 관련 `outputs` 설계·승인·확정·계획·workflow 기록을 원형 그대로 옮겨야 한다. 집 MANUAL도 함께 가져와 비교한다. 문맥 일치가 확인되지 않으면 기존 기록을 보존하고 새 승인 workflow를 사용하며 digest를 변경하지 않는다.
- 아래 과거 원격 handoff의 미검증 항목 중 unittest는 위 286개 결과로 갱신한다. 현재 미완성은 실제 어댑터 생성·검증과 기기 실행이다. 이 환경의 도구 수정·읽기 전용 검토 도구·회귀 테스트·문서를 사용자 요청에 따라 현재 Child에 커밋해 전달한다. 원격 push와 merge는 별도 승인 전까지 하지 않는다. 집의 dirty 변경을 보존하고 새 커밋과 비교해 필요한 수정을 반영한다.
- 잘 작동함: 원격 Child/설정/문서와 thumby 프로필 일치.
- 잘 작동함: 필요한 원격 파일만 가져온 임시 Git 환경에서 문맥 검사 및 프로필 단위 테스트 16개 통과.
- 첫 생성 경로와 요청 계약을 `micropython/ThumbyDodge/`로 고정했고, 실기 런처 규칙에 맞춰 `ThumbyDodge.py`를 필수 엔트리로 요구한다.
- game + thumby 설계 validator가 게임 폴더와 같은 이름의 엔트리 Python 파일을 구조적으로 강제한다.
- 미검증 Thumby 하위 모듈 import(`import thumby.*`, `from thumby.* import ...`)를 gate에서 차단하고 회귀 테스트 2개를 추가했다.
- 엔트리 고정 테스트는 `import sys` → `sys.modules` fake `thumby` 등록 → 엔트리 모듈 import 순서를 profile gate에서 강제해 CPython/Docker의 기기 모듈 부재를 후보 단계에서 차단한다.
- 확인 불가: 추가 테스트를 포함한 현재 Child 전체 회귀, 집의 현재 브랜치·미커밋 상태·현재 outputs 및 실제 Ollama/Docker/기기 결과.
- 개선 후보: 실제 실패 사례가 확인되면 import 부작용·Color 모듈 혼입에 필요한 최소 gate를 보강한다.
- 미구현: 생성 게임을 실제 Thumby `/Games/<GameName>/`로 전송하거나 웹 에뮬레이터를 자동 실행하는 장치 배포 연결.
- 기존 전체 회귀 216개는 이전 Epic의 집 검증 결과다. 현재 Child 전체 회귀를 재검증한 결과가 아니다.
- 최신 프로필/엔트리 계약 보강 후 단위·전체 테스트는 원격 GitHub 연결에서 실행하지 못했으므로 미검증이다.
- 일반 Thumby 공식 API: https://thumby.us/API/Get-Started/
- 허용된 첫 게임 API: buttonL/buttonR.pressed, display.fill/drawFilledRectangle/drawText/update/setFPS.

## 재개에 필요한 자료
- target.json, generation_profile.py, test_generation_profile.py, thumby_dodge_request.json.
- 생성 연결 확인 시 create_loop.py와 해당 호출부만 추가로 읽는다.
- 로컬 outputs/state가 있으면 현재 요청·문맥 SHA와 일치하는지 확인한다.
- Color 자료를 일반 Thumby 입력으로 자동 변환하거나 삭제하지 않는다.
- 승인 설계·테스트·state.json이 있으면 경로와 SHA-256, 생성 문맥을 확인한다.

## 검증 명령·다음 작업
1. 집에서 git branch --show-current, git status --short와 로컬 target.json을 확인한다.
2. ai/personal-game-ai에서:
   - python read_context.py
   - python -m unittest test_generation_profile -v
   - python -m unittest discover -p 'test_*.py'
3. `python workflow.py --request thumby_dodge_request.json`으로 설계 후보를 생성한다.
4. 설계·테스트 후보를 검토하고 표시된 SHA-256으로 승인·확정한 뒤 고정 테스트를 commit한다.
5. 같은 요청을 재실행해 구현과 Docker 검사를 완료하고 실제 Thumby에서 플레이한다.
6. 플레이 의견은 기존 게임 수정 흐름의 다음 Child 입력으로 넘긴다.

## 다음 작업자 handoff

- 현재 작업은 이 Child에서 계속한다. main 통합·merge/rebase·브랜치 삭제는 아직 하지 않는다.
- main과 Git history는 diverged 상태지만 main 쪽 차이는 AGENTS/docs/agent 문서뿐이며 Personal Game AI 코드는 충돌하지 않는다. 현재 Child AGENTS와 main AGENTS의 차이는 MANUAL 기록 방침 한 줄뿐이다. AGENTS는 임의 수정하지 않고, 사용자가 방금 확정한 최신 MANUAL 운용(짧은 사용자용 완료 보고)은 현재 작업부터 따른다.
- 최근 동작 변경 기준 commit: `f79b8c697bb96c6e7bfc18b12a572a202cafabdd`.
- 현재 생성 계약:
  - `ThumbyDodge.py`가 폴더명 엔트리이자 기기 어댑터다.
  - 엔트리 함수 계약에는 실제 런타임 진입 함수 외에 CPython에서 1회 호출하고 끝나는 유한 adapter/helper를 둬 fixed test가 무한 루프 없이 어댑터 동작을 검사할 수 있게 한다.
  - 최소 한 순수 규칙 모듈을 별도로 두고, 그 모듈은 `thumby`를 import하지 않는다.
  - 엔트리는 CPython import-safe이며 MicroPython runtime guard에서 진입 함수를 직접 호출한다.
  - 런처/runtime guard 요구의 fixed unittest는 CPython import-safe 동작을 검사하고, MicroPython guard 존재·직접 호출은 구현 단계 generation profile AST gate가 맡는다.
  - 엔트리 fixed test의 fake-module 계약은 `import sys` 후 `sys.modules['thumby']`에 None이 아닌 fake를 직접 넣고 엔트리를 import하는 순서 하나로 통일한다. profile 테스트 지침은 generic mock 지침 뒤에 적용한다.
  - 테스트 scaffold의 대상 import 문장은 유지하되 그 앞에 `sys` import와 fake 주입을 넣도록 profile prompt에서 명시해 scaffold와 gate의 순서를 일치시킨다.
  - 엔트리 구현 prompt에는 실제 `/Games/ThumbyDodge` sibling 경로를 전달한다.
  - 해당 `sys.path` 추가는 MicroPython 조건 안에서만 수행하도록 안내해 CPython import의 경로 상태를 바꾸지 않는다.
  - `execute_plan`이 통과한 선행 task의 artifact를 재검증하고 실제 검증 코드를 후속 task에 전달한다.
  - dependent request 4000자 제한은 유지한다. generation profile 지침이 붙는 구현 task만 자기 checks가 담당하는 requirement로 축소하고, 기존 non-profile 흐름은 전체 requirements 전달 계약을 유지한다.
  - 요청/작업 문맥이 바뀌면 과거 승인 기록을 재사용하지 않고 새 workflow 기록을 만든다.
- 원격 확인 완료:
  - 공식 TinyCircuits 런처가 `/Games/<폴더>/<폴더>.py`를 import하는 구조와 현재 엔트리 계약이 일치한다.
  - 기존 GitHub Actions/check 실행 경로는 없다. 이 Child에서 CI를 새로 만들지 않는다.
  - legacy workflow 기록 symlink는 state를 읽기 전에 거부하도록 기존 신뢰 경계를 유지한다.
- 현재 추가 구간(`0fa2110d...` 이후)은 Personal Game AI 코드·테스트·작업 MD 7파일만 변경했다. 새 CI나 범위 밖 파일은 추가하지 않았다.
- 아직 미검증:
  - 최신 단위 테스트와 전체 unittest.
  - Docker 검사.
  - 실제 Ollama 설계/테스트/구현 생성.
  - 실제 Thumby 실행.
- 다음 작업 순서:
  1. `git branch --show-current && git status --short && git rev-parse HEAD`
  2. 원격 Child 최신 상태를 반영하고 `cd ai/personal-game-ai`
  3. `python read_context.py`
  4. `python -m unittest test_generation_profile test_test_plan test_workflow test_create_loop test_implementation_link -v`
  5. `python -m unittest discover -p 'test_*.py'`
  6. 통과하면 `python workflow.py --request thumby_dodge_request.json`
  7. 설계 후보를 검토해 SHA로 승인하고, 고정 테스트도 검토 후 SHA로 확정한다.
  8. workflow가 요구하는 고정 테스트 commit 후 같은 요청을 재개해 구현·Docker 검사를 끝낸다.
  9. `micropython/ThumbyDodge/` 결과를 실제 Thumby에서 플레이한다.
- 실패 시 다음 작업자는 **처음 실패한 명령의 전체 오류 + workflow stage/record/review SHA**부터 확인한다. 실제 실패가 없는 상태에서 새 gate나 추측성 호환 규칙을 추가하지 않는다.
- 첫 플레이 이후 자연어 피드백 수정은 다음 책임 단위다. 새 수정 엔진을 만들기보다 기존 `edit_loop`/plan 엔진에 “플레이 의견 → 수정 대상 선택 → 수정/검사”를 연결한다.

검토 도구 추가 검증: 후보 경로·SHA·보호 기록이 없는 검토 단계를 차단하고, 보고 직전 계획 상태 변경도 감지합니다. 두 오판을 회귀 테스트로 재현한 뒤 수정했습니다. 정상 후보는 review_file·review_sha256을 표시하지만 승인하지 않습니다.
