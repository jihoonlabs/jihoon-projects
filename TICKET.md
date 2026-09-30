# Ticket Epic

> Branch context: `feature/ticket-complete`
>
> Repository-wide rules are defined by `AGENTS.md`. Branch-specific state and handoff information belong here.

## 목표

Next.js·React·Zustand와 Laravel API를 연결한 Jira형 칸반 보드를 완성한다.

## 구현 완료 범위

- Laravel: 목록, 상세, 생성, 삭제와 티켓 수정 API를 구현했다.
- PATCH `/api/tickets/{ticket}`은 제목, 설명, 상태, 우선순위, 담당자를 부분 수정할 수 있다. 기존 DnD 상태 변경도 같은 API를 계속 사용한다.
- React: API 응답과 화면 모델의 snake_case/camelCase 변환, 목록 조회, 검색, 담당자 필터, 클라이언트 position 정렬을 구현했다.
- DnD 상태 변경과 동일 티켓 연속 쓰기 직렬화, 낙관적 이동/삭제 및 실패 복구를 구현했다.
- '나' 필터는 인증 스토어의 현재 사용자 ID를 사용한다. 기존 ID 하드코딩은 제거됐다.
- 티켓 생성 모달을 구현하고 헤더의 '+ チケット作成' 버튼에 연결했다.
- 카드에서 드래그 없이 상태를 직접 선택할 수 있다.
- 카드의 편집 UI에서 제목, 설명, 상태, 우선순위, 담당자를 수정할 수 있다.
- 카드 삭제 버튼과 확인 절차를 구현했다.
- 생성/편집 담당자 선택은 현재 로그인 사용자 또는 미할당으로 제한한다. 전체 사용자 선택 API는 이번 범위에 추가하지 않았다.
- 생성/편집 실패 시 폼을 닫지 않고 store 오류를 유지한다. 상태 변경/삭제 실패는 기존 rollback 동작을 사용한다.

## 자동 검증 상태

기존 `feature/ticket` 체크포인트 기준으로 Ticket 관련 35개, React 전체 82개, Laravel 전체 71개 테스트가 통과한 기록이 있다.

이번 `feature/ticket-complete` 작업에서는 Laravel의 일반 티켓 수정 회귀 테스트를 추가했다. 다만 GitHub 원격 편집 환경에서는 Laravel/React 테스트, TypeScript, ESLint, Pint, build를 실제 실행하지 못했다. 따라서 새 변경분은 **테스트 코드 추가/정적 검토 완료, 실행 검증 대기** 상태다.

## 실제 브라우저 검증 상태

아직 미검증이다. 집 로컬에서 다음을 실제 로그인 세션으로 확인한다.

1. 목록 로딩, 검색, '나'/미할당 필터.
2. 티켓 생성 후 즉시 보드 반영 및 새로고침 후 서버 데이터 유지.
3. DnD 상태 변경과 카드 select 수동 상태 변경.
4. 제목/설명/상태/우선순위/담당자 편집 후 새로고침 유지.
5. 삭제 성공 및 새로고침 후 미복원.
6. API 실패 시 생성/편집 폼 유지, 상태 이동/삭제 rollback 및 오류 표시.
7. Sanctum session/CSRF와 suspended 사용자 차단.
8. 모바일/작은 화면에서 카드 액션과 모달 조작 가능 여부.

## 확정된 설계

- Laravel 응답은 snake_case, React 모델은 camelCase를 사용한다.
- API의 숫자 담당자 ID는 React에서 문자열로 변환한다.
- `position`은 현재 클라이언트 정렬 전용이며 DB에는 영속화하지 않는다. 새로고침 시 서버 목록 기준으로 초기화된다.
- 번호, 설명, 담당자는 null을 허용한다.
- 담당자 전체 목록 API는 별도 기능으로 확장하기 전까지 만들지 않는다.
- 오래된 `feature/ticket-ui-modal`은 현재 API/타입과 호환되지 않으므로 병합하지 않고 참고 자료로만 취급한다.

## 남은 작업

- 새 변경분의 React/Laravel 전체 테스트, TypeScript, ESLint, Pint, build, diff check를 로컬 또는 CI에서 실행한다.
- 위 실제 브라우저 체크리스트를 집 환경에서 확인한다.
- 검증 중 결함이 나오면 이 브랜치에서 수정 후 본 문서를 갱신한다.
- 모든 검증이 끝나기 전에는 `main`으로 Ticket Epic을 통합하지 않는다.

## 주요 위치

- React: `react/src/features/tickets/{api,types,store,components,mocks}/`
- Laravel: `laravel/app/Http/Controllers/Tickets/`, `laravel/app/Http/Resources/{Tickets,Users}/`, `laravel/tests/Feature/Ticket/`
