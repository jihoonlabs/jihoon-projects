# 썸비 제작 — Epic

갱신일: 2026-10-08
문서 보유 브랜치: feature/thumby-owner-comment-v1

## 목표와 경계
[제품 목표 v1](../personal-game-ai/GOAL_V1.md)에 따라 일반 Thumby에서 작은 게임 제작 흐름을 완성하고, Thumby Color까지 확장한다. 도구 구현은 개인 게임 AI Epic, 기기·게임 구현은 각 작업 브랜치에서 관리한다. 원본 코드·캐릭터·어셋·시나리오·데이터 복사는 절대 금지하며 장르·플레이 형식·핵심 재미를 기기 제약 안에서 최대한 비슷하게 살리는 독자적인 게임을 제작한다. 이 문서는 연결과 상태를 관리하며 브랜치 merge나 코드 통합 완료를 뜻하지 않는다.

## 작업 연결
| 작업 | 브랜치 | 현재 상태·계약 |
| --- | --- | --- |
| 공통 제작 도구 | feature/personal-game-ai | 설계·고정 테스트·실행 기반. 아래 Child의 코드 통합은 별도 검토 |
| 일반 Thumby 생성 | feature/personal-game-ai-thumby-generation | rules.py와 어댑터 분리. 집에서 규칙 테스트 6개 통과 보고; 어댑터 pending. 집 산출물·승인 기록은 원격 존재를 가정하지 않음 |
| 자연어 입력 | feature/personal-game-ai-request-intake | 입력·누락 질문·명시적 설정. 게임·기기 조사 기능은 미구현 |
| 입력·제작 연결 | feature/personal-game-ai-workflow-bridge | 명시적 실행기 연결·질문 답변·검토 전달. 실제 Ollama 연결은 집에서 검증 필요 |
| 제품 방향 정리 | feature/thumby-owner-comment-v1 | GOAL 이동·보완과 이 Epic 문서. 코드 변경 없음 |
| Thumby Color | feature/thumby-color | 기존 브랜치 존재만 확인. 자동 제작 도구의 Color 지원·연결·실기 검증은 미완료 |

## 다음 순서와 완료 조건
1. 집의 기존 규칙·테스트·승인·outputs를 보존하고 원격 변경과 비교한다. 일반 Thumby 어댑터 요청 길이와 JSON 축약을 확인하여 생성·고정 테스트·실기 플레이를 완료한다.
2. 승인된 작은 게임 하나로 자연어 입력에서 제작·재개까지 실제 연결을 검증한다. 실제 모델 검증과 모의 검증을 구분한다.
3. 게임 조사·기기 조사·한계 분석·선택지·명세 승인을 도구 입력 흐름에 연결한다. 출처와 확인 불가 항목을 저장한다.
4. 일반 Thumby에서 규칙/어댑터 계약을 검증한 뒤 Color 전용 프로필·어댑터·검사를 구현한다. API·자원 예산·실기 결과를 확인하기 전 지원 완료로 표시하지 않는다.

새 기획 결정은 사용자에게 확인하며, 승인 범위의 구현·수정은 이어간다. 각 Child가 검증과 한계를 기록하고, Epic은 실제 채택 SHA와 통합 상태를 기록한다. 현재 채택/merge SHA는 없다.

## 재개 문서
도구 Epic의 [원격 문서](https://github.com/jihoonlabs/jihoon-projects/blob/feature/personal-game-ai/docs/personal-game-ai/EPIC.md)를 시작점으로 사용한다. 게임 생성·입력·연결의 작업 MD와 MANUAL은 각 해당 브랜치의 docs/personal-game-ai/에 있다. 브랜치가 다르므로 현재 체크아웃에 모두 존재한다고 가정하지 않는다.
