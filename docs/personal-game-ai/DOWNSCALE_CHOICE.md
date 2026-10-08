# 축소안·선택 기록 Child

브랜치: feature/personal-game-ai-downscale-choice
기반 원격: acdbc1b9aba48b761727e35ef810296904d48ca4
방향: 1차 제작 도구, 2차 경험을 활용한 자체 제작·개선. 모델 학습 완료로 표현하지 않는다.

## 결과·경계
downscale_choice.py가 조사된 기획과 2~3개 제안안을 받아 비교·선택 결과를 새 파일에 저장한다. 선택지는 유지할 재미, 축소할 요소, 미검증 항목을 각각 포함해야 한다. 사용자 선택과 최종 명세 승인을 구분한다.
조사 자료·원본 복사 금지 정책을 재검사하고 기기 혼용·중복 ID·없는 선택을 차단한다. 원본 기획·제안과 기존 출력은 보존한다. 기존 engine·게임·승인 digest는 변경하지 않는다.

## 계약
게임 형식·기기 조사 항목이 모두 필요하다. unknown 항목도 허용하지만 구현 가능성은 not_assessed로 유지한다. 제안 JSON은 device/options, 안별 id/title/keep/reduce/unverified를 갖는다. --select는 사용자의 선택을 전달하는 명시 입력이며 --interactive는 화면에 안을 비교 표시하고 ID를 받는다. 선택 전 needs_choice, 선택 후 needs_specification, specification_approved=false다.
제안 내용의 사실·권리·실현 가능성을 구조 검사만으로 보장하지 않는다. 모델 제안 자동 생성과 명세 승인·제작 연결은 후속 범위다. 현재 이 파일은 workflow 요청이 아니다.

## 검증·재개
관련 52개 검사 통과. 선택과 승인 분리, 축소·미검증 공개, 자료 누락·기기 혼용·중복·잘못된 선택 차단, 입력 보존 확인. MANUAL에 CLI와 제안 형식 예제를 기록한다. 실제 Ollama·Docker·화면 검사 미실행.
다음은 선택안으로 검토할 명세를 작성하고 사용자가 확인한 화면·조작 기본값을 기록하는 단계다. 승인 후 반복 제작에 활용하고 성공·실패·사용자 평가를 축적하되, 자료 저장과 모델 자체 학습을 구분한다.
commit·일반 push 허용, merge 금지.
