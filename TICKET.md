# Ticket Epic

## 목표

Next.js·React·Zustand와 Laravel API를 연결한 Jira형 칸반 보드를 완성한다.

## 현재 상태

- Epic 브랜치: `feature/ticket`. API ↔ React 정합성 구현은 `23f5178`까지 commit/push되어 있다.
- Laravel: 목록·상세·생성·상태 변경·삭제 구현. 목록·단건 응답은 Resource의 `data` 구조를 사용한다. DELETE는 message를 반환한다.
- React: API 응답 타입·화면 Ticket·생성 입력 타입을 분리하고 API 경계 변환을 적용했다. 담당자 ID는 화면에서 문자열로 통일한다.
- 보드의 검색·null 표시·클라이언트 position 정렬, 생성 요청의 assignee_id 변환, PATCH 성공 응답 반영을 구현했다.
- 동일 티켓 쓰기는 순차 처리하고 연속 DnD의 마지막 드롭 의도를 보존한다. 쓰기와 겹쳐 폐기한 조회는 쓰기 완료 후 재실행한다.
- 낙관적 삭제·열 이동 중 원래 position을 예약하여 실패 복구 시 순서를 보존한다. 복구는 해당 티켓에 한정한다.
- 생성·삭제 UI와 열 내부 드롭 위치 기반 재정렬은 미구현이다. ‘나’ 필터 수정은 별도 브랜치 `feature/ticket-me-filter`에 있으며 Epic에는 아직 통합하지 않았다.

## 확정된 설계·UX

- Laravel 응답은 snake_case, React 모델은 camelCase를 사용한다. Resource의 data 래퍼와 문자열 티켓 ID는 유지한다.
- API의 숫자 담당자 ID는 React에서 문자열로 변환하고 생성 시 assignee_id로 전달한다.
- `position`은 클라이언트 정렬용으로 유지한다. 현재 DB/API에는 순서 필드를 두지 않으며, 순서 영속화 작업에서 추가한다.
- 최초 API 순서로 열별 position을 부여한다. 생성·열 이동 티켓은 해당 열 끝에 배치한다.
- 재조회 시 같은 열에 남은 티켓의 position을 보존하고 새 티켓·서버에서 열이 바뀐 티켓은 끝에 배치한다.
- 순서는 메모리에서만 유지하며 새로고침 시 초기화한다. 로컬 저장은 사용하지 않는다.
- 번호·설명·담당자는 null을 허용한다. 누락 번호는 ‘—’로 표시하고 번호 검색에서는 제외한다.

## 현재 작업과 검증

정합성 및 리뷰 결함 3건 수정 완료. 결함 재현 실패를 확인한 회귀 테스트를 포함하여 Ticket 관련 35개, React 전체 82개, Laravel 전체 71개 테스트 통과.
TypeScript 검사·ESLint·변경 PHP 파일 Pint·git diff 공백 검사 통과.
연속 드롭은 보드 핸들러와 실제 스토어를 연결한 테스트로 검증했다. 실제 브라우저의 포인터 조작·서버 연동 검증은 아직 수행하지 않았다.

## 생성·삭제 UI 기존 브랜치 검토

- `feature/ticket-ui`는 현재 Epic의 이전 기반이며 별도 생성·삭제 UI 변경은 없다.
- `feature/ticket-ui-modal`은 생성·수정 폼, 카드 수정·삭제 버튼, 삭제 확인 모달과 공통 모달을 포함한다. 현재 Epic의 API·스토어·타입 변경 이전에서 갈라졌으므로 그대로 병합할 수 없다.
- 기존 폼은 가짜 문자열 담당자 ID, 현재 타입에 없는 `URGENT` 우선순위, 현재 서버에 없는 `PUT` 수정 요청을 사용한다. 삭제 모달은 스토어가 실패를 내부에서 처리하는 현재 계약과 성공 판정 방식을 맞춰야 한다.
- 재사용한다면 레이아웃 참고로 한정하고, 현재 `CreateTicketInput`과 `addTicket`·`deleteTicket` 계약에 맞춰 구현한다. 수정 UI는 별도 API 설계가 필요하다.

## 다음 작업

1. 실제 로그인 세션에서 목록·검색·열 이동·재조회·새로고침 동작을 확인한다.
2. `feature/ticket-me-filter`를 검토한 뒤 Epic에 통합한다. 집 로컬의 미푸시 변경과 먼저 대조한다.
3. 생성·삭제 UI 범위와 담당자 선택 방식을 결정한 뒤 현재 API 계약에 맞춰 구현한다.

## 사용자 판단 사항

이번 정합성 범위의 미결 사항은 없다. 생성·삭제 UI에서 생성·삭제만 먼저 구현할지, 서버에 없는 일반 수정 기능까지 설계할지 결정이 필요하다. 담당자 선택 UI의 데이터 출처도 확정해야 한다. 향후 순서 영속화 설계는 별도 작업에서 확정한다.

## 주요 위치와 유지 원칙

- React: `react/src/features/tickets/{api,types,store,components,mocks}/`
- Laravel: `laravel/app/Http/Resources/{Tickets,Users}/`, `laravel/tests/Feature/Ticket/`
- 작업 브랜치 → `feature/ticket` → `main` 순으로 승인된 범위에서 통합한다.
- 공통 규칙은 AGENTS.md를 따른다. 다음 작업에 필요한 상태·결정만 유지하고 완료된 과정은 누적하지 않는다.
