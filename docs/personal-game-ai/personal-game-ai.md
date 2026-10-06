# 개인 게임 AI — Router

브랜치: feature/personal-game-ai

## 목표
로컬 Ollama 기반 개인 AI가 게임 개발 작업을 작은 책임 단위로 설계·구현·검증하고, 새로운 설계 판단이나 불확실성이 있을 때만 사용자에게 질문할 수 있는 작업 기반을 만든다.

## 현재 작업
- 컨텍스트 구조 정상화 — feature/personal-game-ai-context-router — 진행 중
- 중단 실행 복구 — feature/personal-game-ai-run-recovery — 재정렬·검증 필요
- 실행 이벤트 로그 — feature/personal-game-ai-run-log — 재정렬·검증 필요
- 검증된 게임 경험 학습 — 담당 브랜치 미정 — 대기

## 다음 기준
- 각 구현 브랜치는 하나의 명확한 책임만 가진다.
- 검증된 Child만 이 Epic에 통합한다.
- 상세 구현·검증 이력은 구현 담당 브랜치가 소유하며 이 Router에 중복하지 않는다.
- 다음 작업은 현재 Child의 검증·통합이 끝난 뒤 결정한다.
