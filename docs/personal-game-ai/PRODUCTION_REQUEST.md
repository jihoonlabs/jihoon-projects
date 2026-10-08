# 승인 명세 → 생성 요청 Child

브랜치: feature/personal-game-ai-production-request
기반: 85a53a1c45e481a9933639689b99c4339fe94da2

## 책임·계약
production_request.py는 명시 승인 명세를 다시 검증하고, 일반 Thumby의 선택한 게임 경로·브랜치와 대상 설정을 대조한다. read_context로 실제 Git 루트·브랜치·작업 문서를 확인한다. 새 게임 폴더는 비어 있어야 하며 삭제된 추적 파일도 거부한다. 기존 target.json·게임·승인·출력을 변경하지 않는다.

생성기 입력은 기존 goal/requirements/area 세 필드다. 선택안과 기획 설정은 goal에, 상세 일곱 구역의 모든 문자는 순서대로 requirements에 전달한다. 500자 조건 길이에 맞게 분할하되 목표 4000자·고유 조건 12개 제한을 넘으면 절단·요약 없이 차단한다. 조사 원문·미선택안은 생성 요청에 중복 삽입하지 않는다. 제품 명세 digest는 binding.json에 남기며 기존 설계·테스트 승인으로 승계하지 않는다.

CLI는 새로운 출력 폴더에 request.json과 binding.json을 저장한다. binding은 준비 시점의 설정·문맥 digest와 경로 기록이다. 기존 workflow가 binding을 읽거나 실행 시 제품 승인을 재검증하는 기능은 아직 없다. 실행·모델·Docker·Git 변경은 호출하지 않는다.

## 검증·현재 상태
신규 9개 검사와 기획·조사·선택·명세·bridge 회귀 총 49개 통과. 실제 Git 임시 저장소에서 브랜치 불일치, 기존 게임·삭제된 추적 파일·symlink 차단, 승인 변경 차단, 상세 문자 보존, 제한 초과와 출력 덮어쓰기 차단을 확인했다. Python 3.12 실행 및 3.9 문법 호환 검사 실시.
집 Mac의 파일·승인 명세, 실제 Ollama·Docker·Thumby는 접근/검증하지 않았다. 현재 thumby 프로필은 좌우 버튼·제한된 표시 API용이며 RPG의 다른 버튼·저장 API 확장은 미완료다. Color 요청은 차단한다. 다음은 검증된 일반 Thumby 입력·저장 API를 생성 프로필과 테스트에 연결하는 작업이다.
