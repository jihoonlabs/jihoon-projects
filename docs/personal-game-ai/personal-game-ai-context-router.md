# 개인 게임 AI — 컨텍스트 Router 정규화

브랜치: feature/personal-game-ai-context-router

## 책임
현재 Git 브랜치에서 전용 MD 경로를 자동 결정해, AGENTS.md와 현재 브랜치 MD 및 명시적으로 필요한 코드만 작업 컨텍스트로 사용한다.

## 결정
- 전용 MD는 `docs/personal-game-ai/<브랜치명에서 종류 prefix를 제거한 이름>.md`를 사용한다.
- `target.json`은 특정 branch MD를 고정하지 않고 project만 지정한다.
- 부모·형제·과거 작업 MD는 자동으로 읽지 않는다.
- 게임 품질을 높이기 위한 장기 학습/경험은 작업 MD와 분리된 후속 책임으로 다룬다.

## 범위
- `read_context.py`의 branch MD 자동 선택.
- `target.json`의 고정 문서 의존 제거.
- 관련 컨텍스트 선택 테스트.

## 제외
- 과거 문서 삭제·이관.
- 장기 학습 저장소 구현.
- 실행 복구·로그 기능 수정.
