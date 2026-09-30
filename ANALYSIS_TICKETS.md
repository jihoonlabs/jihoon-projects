# 티켓(Task) 관리 파트 핵심 리뷰 (ANALYSIS_TICKETS.md)

## 1. 핵심 코드 흐름 (1줄 요약)
`tickets/page.tsx` (보드) ➔ `useTicketStore.ts` (Zustand 낙관적 UI 스토어) ➔ `ticketApi.ts` (API 호출) ➔ `Laravel` (`/api/tickets` CRUD)

---

## 2. 🌟 잘 구현된 부분 (Positive Note)
* **`useTicketStore.ts`의 낙관적 업데이트(Optimistic UI) & 복구(Rollback)**: 
  * 드래그 앤 드롭 또는 삭제 시 UI를 즉시 변경한 뒤 API를 부르고, 백엔드 실패 시 원래 위치로 정확히 복구(Rollback)하는 구조가 매우 깔끔하게 되어 있습니다.

---

## 3. ⚠️ Jira급 프로덕션을 위한 필수 수정 항목 (Critical Issues)

### 1) 티켓 순서(Position/Sort Order) 백엔드 영속화 부재
* **현상**: `position` 계산 및 순서 유지가 순수 클라이언트 메모리(`endPosition`, `mergeTickets`) 상에서만 이루어짐.
* **문제**: 칸반 보드 내에서 티켓의 순서를 위/아래로 바꿨을 때 백엔드 DB에 순서(`sort_order` / `position`)가 저장되지 않음. 새로고침을 하거나 다른 팀원이 접속하면 카드 순서가 초기화됨.
* **조치**: 백엔드 DB에 `position` 컬럼 추가 및 `PATCH /api/tickets/reorder` API 구현 필요.

### 2) 422 유효성 검사 에러 메시지 덮어쓰기 (`ticketApi.ts`)
* **현상**: [ticketApi.ts](file:///c:/Users/park.jihoon/simple%20app/JIHOON-PROJECTS/react/src/features/tickets/api/ticketApi.ts#L48)의 `resource<T>` 함수에서 `!response.ok`를 만나면 서버가 보내준 상세 필드 에러(`data.errors`)를 무시하고 단일 에러(`チケット操作に失敗しました (422)`)를 throw함.
* **문제**: 티켓 생성/수정 시 제목 누락 등 유효성 검사 실패 시 모달 창에 어떤 필드가 잘못되었는지 구체적으로 표시되지 않음.
* **조치**: `response.status === 422` 수신 시 서버의 `data.errors` 파싱 로직 추가.

### 3) 동시 수정 충돌 감지(Optimistic Locking) 부재
* **현상**: API 및 타입 정의(`TicketResponse`, `UpdateTicketInput`)에 `version` 또는 `updated_at` 검증 파라미터가 없음.
* **문제**: 2명의 팀원이 동일한 티켓을 동시에 편집 시, 나중에 저장한 사람의 내용이 이전 사람의 수정 사항을 덮어씌워 유실(Lost Update)됨.
* **조치**: 백엔드/프론트엔드 간 `version` 헤더 또는 `updated_at` 필드 기반 동시성 검증 추가.

### 4) 멀티유저 실시간 동기화(WebSocket / Polling) 부재
* **현상**: 다른 팀원이 카드를 이동하거나 생성해도 화면에 즉시 반영되지 않음.
* **문제**: 협업 도구(Jira) 특성상 타 팀원의 작업 내역을 수동 새로고침하기 전까지 알 수 없음.
* **조치**: Pusher / Laravel Reverb / WebSockets를 활용한 실시간 이벤팅 동기화 추가 필요.
