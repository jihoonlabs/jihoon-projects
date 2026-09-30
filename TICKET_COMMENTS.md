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
- Laravel feature tests 8개 통과 (26 assertions), 댓글 범위 Pint 통과: 생성/목록, validation, 작성자 위조 방지, suspended/guest, 권한, 다른 Ticket 접근.
- React comment type/API client 구현.
- Ticket 편집 modal에 댓글 목록/작성/수정/삭제 UI 및 상호작용 테스트 연결. React API/UI 관련 테스트 15개 통과.
- 댓글 파일 ESLint/Prettier, TypeScript 검사, production build 통과.
- 전체 React lint는 기존 `TicketModal/index.tsx`의 effect 내 동기 상태 설정에서 실패한다. 해당 modal 초기화 코드는 댓글 작업 전부터 존재한다.
- 격리된 SQLite DB의 테스트 사용자로 Headless Chrome에서 Sanctum 로그인·CSRF 및 댓글 작성/수정/삭제 확인.

## 남은 작업

1. 기존 Ticket modal lint 오류를 정리한 뒤 전체 lint를 재검증.
2. 검증 완료 후 Ticket Epic으로 통합.
