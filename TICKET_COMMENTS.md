# Ticket Comments

> Branch context: `feature/ticket-comments`
>
> Common rules: `AGENTS.md`. This document is the only feature context for this branch.

## 목표

Ticket에 실제 협업용 댓글 기능을 추가한다. 댓글은 인증 사용자와 Ticket에 귀속되며 작성자 정보와 작성 시각을 제공한다.

## 범위

- Laravel 댓글 DB/model/relation/API
- 인증·active 사용자만 댓글 조회/작성
- 본인 댓글의 수정/삭제 권한
- Ticket 상세에서 사용할 댓글 응답 계약
- Laravel feature tests
- React API/UI 연결은 backend 계약 확정 후 같은 브랜치에서 진행

## 확정 원칙

- 기존 Ticket CRUD/DnD 계약을 깨지 않는다.
- 작성자 ID는 로그인 세션에서 결정하며 클라이언트 입력을 신뢰하지 않는다.
- 다른 사용자의 댓글 수정/삭제는 서버에서 거부한다.
- 구현 완료와 테스트 실행 완료를 구분한다.

## 현재 상태

- 브랜치 생성 및 작업 범위 정의.
- 구현/자동 테스트/브라우저 검증은 아직 시작 전.

## 다음 작업

1. 기존 Ticket migration/API 패턴 확인.
2. comments schema와 관계 구현.
3. API와 권한 테스트 추가.
4. React 연결 및 UI 테스트.
5. 검증 완료 후 Ticket Epic으로 통합.
