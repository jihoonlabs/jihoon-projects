# 장르·기기 입력 Child

브랜치: feature/personal-game-ai-game-brief
기반: workflow bridge 원격 46c30b199a88c52747e1ebb18233dd42c2cd4722
방향: owner 브랜치 GOAL_V1.md 확정 방향. 일반 Thumby 우선·Color까지 확장, 원본 복사 금지.

## 결과와 경계
game_brief.py로 기기와 장르·핵심 재미를 받고 누락된 설정만 질문한다. 일반 Thumby와 Color를 구분하여 조사 전 기획 JSON을 저장한다. 기존 request_intake·workflow·target.json·게임·승인 기록은 변경하지 않는다.

제품 목표는 확정 방향이며 단순 참고 제안이 아니다. 장르 목록의 제작 순서와 세부 기획은 미확정이다. 기기 선택 지원과 해당 기기의 게임 생성 지원은 구분한다.

## 계약
- schema_version=1. 입력은 device=thumby/thumby-color, settings=genre/experience만 허용한다.
- 원문 설정 1~1000자. 누락 설정이 있으면 needs_settings, 모두 받으면 needs_research다.
- 연구·실측·승인 이전에 생성 요청을 만들지 않는다. feasibility=not_assessed, specification_approved=false다.
- 정책에는 독자 표현·원본 복사 금지와 플레이 형식의 유사성 목표를 기록한다. 정책 필드만으로 출력물의 준수를 보장하지 않는다.
- --output은 완성된 입력만 새 파일에 저장하며 기존 파일은 덮어쓰지 않는다. 모델·Git·Docker 호출 없음.

## 검증·다음 작업
입력/연결 관련 39개 검사 통과. 기기 구분·승인 오표시 방지·누락 질문·잘못된 입력·파일 보존·CLI 저장을 확인했다. 실제 모델·기기 조사는 미실행이다.
다음은 조사 근거·기기 제약을 이 기획에 연결하고 축소 선택지·명세 승인까지 연결하는 별도 책임이다. 현재 JSON을 workflow.py --request에 넘기지 않는다.
commit·push 허용, merge 금지. 집에서는 MANUAL의 짧은 명령으로 재현한다.
