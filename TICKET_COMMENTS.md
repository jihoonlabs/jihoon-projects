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
- Ticket 편집 화면의 댓글 조회/작성/수정/삭제 UI
- Laravel feature tests 및 React API/UI tests

## 확정 원칙

- 기존 Ticket CRUD/DnD 계약을 깨지 않는다.
- 작성자 ID는 로그인 세션에서 결정하며 클라이언트 입력을 신뢰하지 않는다.
- 다른 사용자의 댓글 수정/삭제는 서버에서 거부한다.
- 댓글 body는 trim 후 빈 문자열을 거부하고 최대 5000자로 제한한다.
- 구현 완료와 테스트 실행 완료를 구분한다.

## 현재 상태

- 댓글 migration/model 및 Ticket/User relation 구현.
- 댓글 목록/작성/수정/삭제 Laravel API 구현.
- 댓글 작성자는 세션 사용자와 명시적으로 연결하며 payload의 user_id는 사용하지 않는다.
- guest/suspended 접근 차단 및 작성자 전용 수정/삭제 권한 구현.
- Laravel feature tests 추가: 생성/목록, validation, 작성자 위조 방지, suspended/guest, 권한, 다른 Ticket 접근.
- React comment type/API client 구현.
- Ticket 편집 modal에 댓글 목록/작성/수정/삭제 UI 연결.
- React API tests 추가: mapping, CSRF write, delete, HTTP/error envelope.
- 위 신규 테스트는 아직 실제 실행하지 않았다.
- 실제 브라우저 검증도 아직 수행하지 않았다.

## 남은 작업

1. React 댓글 UI interaction tests 추가.
2. Laravel/React 관련 테스트 실제 실행 및 실패 수정.
3. lint/build 확인.
4. 실제 브라우저에서 댓글 생성/수정/삭제 및 권한/오류 동작 확인.
5. 검증 완료 후 Ticket Epic으로 통합.
