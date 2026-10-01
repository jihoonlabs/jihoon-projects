# 개인 게임 AI — 기반 연결

갱신일: 2026-10-01
작업 브랜치: feature/personal-game-ai-foundation
부모 Epic: feature/personal-game-ai

## 목적
로컬 Ollama를 사용하는 개인 게임 제작 도우미를 만든다.
승인된 작업은 진행하고 중요한 설계 결정은 사용자에게 질문한다.
외부 유료 API는 사용하지 않는다.

## 이번 Child 범위
- 기존 AI 프로그램을 전용 작업 공간으로 정리한다.
- 대상 worktree와 예상 브랜치를 명시한다.
- 대상의 AGENTS.md와 현재 Child 전용 MD를 읽는다.
- 지정한 코드만 추가로 읽어 분석 요청을 전달한다.
- 분석 결과를 저장하며 게임 파일은 수정하지 않는다.

## 현재 상태
- Ollama 0.35.0, qwen3-coder:30b 설치 확인.
- 기존 위치에서 요청·응답 저장·코드 추출·문법 검사 확인.
- 고정된 두 함수의 기능 검사 13개 통과.
- tasks.json과 생성 결과는 복사하지 않았다.
- 새 worktree에서 대상 브랜치 확인과 지정 파일 3개 읽기 성공.
- 로컬 AI에 자료를 전달하고 분석 결과 저장 성공.
- 분석에는 근거가 부족한 표현이 있어 사용자 검토가 필요하다.
- 게임 파일 수정·테스트 실행·Git 자동 작업 기능은 아직 없다.
- 예상 브랜치 불일치 시 중단 확인.
- 지정 파일 누락 시 중단 확인.
- 두 검사는 파일·브랜치 변경과 모델 호출 없이 수행했다.
- 이번 커밋은 AI 요청·연결 확인·대상 자료 읽기·분석 저장 기능만 포함한다.
- 기존 시험용 파일은 로컬에 보존하며 이번 커밋에서 제외한다.

## 대상 게임
- worktree: /Users/parkjihoon/workspace/period-action-worktree
- 예상 브랜치: feature/period-action-foundation
- 지침: AGENTS.md
- 작업 문서: docs/period-action/FOUNDATION.md
- 코드: micropython/LanternRun/lantern_core.py

## 제한
- 다른 MD와 과거 응답을 자동으로 읽지 않는다.
- 브랜치 불일치 시 모델 호출 전에 중단한다.
- 다른 worktree의 파일을 수정하지 않는다.
- 생성 코드를 자동 실행하지 않는다.
- 자동 수정·재시도·질문 생성·Git 통합은 아직 미구현이다.
- 문맥 한도와 응답 잘림을 확인해야 한다.

## 다음 작업
이번 Child 결과를 Epic 전용 MD에 요약하고 Epic에 통합한다.
후속 Child에서 대상 경로 설정과 문맥 분량 검사를 확장한다.
