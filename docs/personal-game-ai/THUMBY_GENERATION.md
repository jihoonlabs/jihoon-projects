# 개인 게임 AI — 일반 Thumby 자동 제작 연결

## 목적·범위
- 현재 Child: feature/personal-game-ai-thumby-generation
- 작은 일반 Thumby 게임의 자동 생성·검사 연결만 담당한다.
- 첫 검증 게임: 좌우 이동·장애물 충돌·점수·재시작.
- 규칙은 순수 Python, 기기 입력·표시는 별도 어댑터로 나눈다.
- Color·StarCraft와 기존 게임 수정은 이번 범위 밖이다.

## 작업 기준
- AGENTS.md + 이 문서 + 필요한 코드/산출물로 재개한다.
- 시작 전 Git 상태·브랜치·설정·승인 대상을 확인한다.
- 확정 범위의 구현→검사→수정→재검사는 자율 진행한다.
- 새 설계·범위·구조 변경은 근거·추천·영향을 설명하고 승인받는다.
- 기존 변경·untracked·산출물·stash를 보존한다.
- MD는 현재 계약과 상태 중심으로 유지하며 경과를 append하지 않는다.
- AGENTS 변경과 MD 추적·전달 방식 변경은 별도 결정이다.
- 원격 작업은 이 Child 범위에 한정한다. main 통합·브랜치 삭제는 하지 않는다.
- 도구와 플랫폼→게임 Epic→게임 Child의 분리 계약을 유지한다.

## 실행 계약
- ai/personal-game-ai/target.json:
  - expected_branch: feature/personal-game-ai-thumby-generation
  - branch_document: docs/personal-game-ai/THUMBY_GENERATION.md
  - generation_profile: thumby
  - code_files: [] (다른 기능 MD를 추가하지 않는다)
- edit_directory는 아직 미지정이다. 실제 game 생성 요청은 경로 확정 전 실행하지 않는다.
- workflow.py: 요청→설계 검토→테스트 검토→설치→Git 준비→계획→구현.
- 승인·확정 SHA-256, 고정 테스트 Git 보호, Docker 검사 계약을 유지한다.
- generation_profile.py의 프롬프트 및 AST 검사는 game + thumby에서만 적용된다.
- 집의 Ollama·Docker·실제 기기는 원격 GitHub 연결만으로 실행되지 않는다.
- 기존 승인/실행 기록은 생성 당시 문맥에 묶여 있으므로 문서 변경 후 임의로 재사용하지 않는다.

## 강제 검사와 지침의 구분
- read_context.py는 실제 브랜치, 문서 경로, 문맥 분량과 지정 파일을 검사한다.
- generation_profile.validate_code 검사는 create_loop.py의 후보 저장 전 호출된다.
- AST 검사 범위: thumbyColor 이름 import, thumby 별칭/from import, 일부 직접 API 속성, 최상위 while True.
- 모든 Color 모듈·간접 API 접근·import 중 루프 실행을 포괄적으로 차단하는 검사는 아니다.
- 순수 규칙/어댑터 분리는 현재 프롬프트 지침이며 전체 의미를 강제하는 gate는 아니다.
- 검사 통과가 MicroPython 호환성·게임 품질·실행 안전성을 보장하지 않는다.

## 현재 진단·검증
- 잘 작동함: 원격 Child/설정/문서와 thumby 프로필 일치.
- 잘 작동함: 필요한 원격 파일만 가져온 임시 Git 환경에서 문맥 검사 및 프로필 단위 테스트 16개 통과.
- 실제 문제: 기존 문서의 검사 범위 과장과 오래된 검증 기록을 바로잡았다.
- 확인 불가: 집의 현재 브랜치·미커밋 상태·Color 사양/tasks·outputs 및 실제 Ollama/Docker/기기 결과.
- 개선 후보: 실제 실패 사례가 확인되면 import 부작용·Color 모듈 혼입에 필요한 최소 gate를 보강한다.
- 기존 전체 회귀 216개는 이전 Epic의 집 검증 결과다. 현재 Child 전체 회귀를 재검증한 결과가 아니다.
- 일반 Thumby 공식 API: https://thumby.us/API/Get-Started/
- 허용된 첫 게임 API: buttonL/buttonR.pressed, display.fill/drawFilledRectangle/drawText/update/setFPS.

## 재개에 필요한 자료
- target.json, generation_profile.py, test_generation_profile.py.
- 생성 연결 확인 시 create_loop.py와 해당 호출부만 추가로 읽는다.
- 로컬 요청/사양/tasks는 현재 Child용 입력인지 확인한 뒤 사용한다.
- Color 자료를 일반 Thumby 입력으로 자동 변환하거나 삭제하지 않는다.
- 승인 설계·테스트·state.json이 있으면 경로와 SHA-256, 생성 문맥을 확인한다.

## 검증 명령·다음 작업
1. 집에서 git branch --show-current, git status --short와 로컬 target.json을 확인한다.
2. 로컬 사양/tasks의 플랫폼·요청 영역·대상 경로를 확인해 일반 Thumby 범위와 비교한다.
3. ai/personal-game-ai에서:
   - python read_context.py
   - python -m unittest test_generation_profile -v
   - python -m unittest discover -p 'test_*.py'
4. 입력 범위와 실제 게임 경로를 확정한 후 설계·테스트 후보를 생성한다.
5. 새로운 세션은 이 문서의 계약·검증·미해결 항목으로 재개하며 부모/형제 MD를 추가하지 않는다.
