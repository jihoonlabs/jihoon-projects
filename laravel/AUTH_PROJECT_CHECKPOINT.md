# チケット機能チェックポイント

最終更新：2026-09-24
作業ブランチ：`feature/ticket-api`

## 本日完了した作業

### 1. Laravel Ticket API

以下のAPIを実装済み。

- `GET /api/tickets`
- `POST /api/tickets`
- `GET /api/tickets/{ticket}`
- `PATCH /api/tickets/{ticket}`
- `DELETE /api/tickets/{ticket}`

チケット作成時：

- `issue_key` は `TICK-{id}` 形式で生成
- `status` 未指定時は `TODO`
- `priority` 未指定時は `MEDIUM`
- priority:
  - `HIGHEST`
  - `HIGH`
  - `MEDIUM`
  - `LOW`
  - `LOWEST`

`issue_key` をDBのID確定後に設定するため、nullable化する追加migrationを作成済み。

### 2. Ticket API認証

`routes/api/tickets.php` に以下を適用済み。

- `auth:sanctum`
- `active.user`

そのためTicket APIはログイン済みかつactiveユーザーのみ利用可能。

認証テスト：

- 未認証ユーザー → `401`
- suspendedユーザー → `403`
- activeユーザー → CRUD利用可能

### 3. Laravel Ticket tests

以下に分割済み。

- `tests/Feature/Ticket/StoreTest.php`
- `tests/Feature/Ticket/IndexTest.php`
- `tests/Feature/Ticket/ShowTest.php`
- `tests/Feature/Ticket/UpdateStatusTest.php`
- `tests/Feature/Ticket/DestroyTest.php`
- `tests/Feature/Ticket/AuthenticationTest.php`

Ticket CRUDテストではactiveユーザーを作成し、`actingAs()` で認証して実行。

Laravel全体テスト結果：

69 tests / 273 assertions PASS

### 4. React useTicketStore

`useTicketStore.ts` のAPI通信を修正。

GET:
- `credentials: 'include'` を追加

POST:
- `fetchWithCsrf()` を使用

PATCH:
- `fetchWithCsrf()` を使用
- DnD用のOptimistic Update
- API失敗時rollback

DELETE:
- `fetchWithCsrf()` を使用
- Optimistic Delete
- API失敗時rollback

catchの型はすべて `unknown` に統一し、
`@typescript-eslint/no-explicit-any` を解消。

`deleteTicket` の型：

`(id: string) => Promise<void>`

React lint結果：

`pnpm lint` PASS

## UIの現在状況

Kanban UI / DnDは既に実装済み。

ただし以下はまだUI未実装：

- チケット作成UI
- チケット削除UI

予定：

- 作成 → Modal
- 削除 → カードメニュー等から確認Dialog

Store/API側の `addTicket()` / `deleteTicket()` は準備済み。

## 次に確認する箇所

最優先：

`react/src/features/tickets/types/ticket.ts`

React側のTicket型を確認した結果、Laravel APIレスポンスとの命名差異を確認済み。

Laravel API：

- `issue_key`
- `created_at`
- `updated_at`

React Ticket型：

- `issueKey`
- `createdAt`
- `updatedAt`
- `position`

また、React側では `id: string` だが、Laravel側のIDは数値。

現在 `useTicketStore.ts` ではLaravelのレスポンスをそのままstateへ格納しているため、
APIレスポンスとReactのTicket型をどの層で変換するかを次回最初に検討する。

# 📌 作業引き継ぎ・進捗メモ

## 1. 概要 & 検討事項 (次回最初に対応)
現在 `useTicketStore.ts` では Laravel のレスポンス（`TicketResource`）をそのまま State へ格納しているため、
**API レスポンス（snake_case）と React の Ticket 型（camelCase）をどの層（API Client層 / Store層 / Adapter関数）で変換するか**を次回最初に検討・実装する。

---

## 2. 本日の作業完了内容
- [x] **공통 및 도메인 모달 컴포넌트 작성**
  - `src/shared/components/BaseModal` (공통 모달 껍데기)
  - `src/features/tickets/components/Modal/FormModal` (티켓 생성/수정 모달)
  - `src/features/tickets/components/Modal/DeleteModal` (티켓 삭제 확인 모달)
- [x] **Card 컴포넌트 이벤트 처리**
  - 카드 호버 시 나타나는 수정(✏️) / 삭제(🗑️) 버튼 추가
  - `@dnd-kit` 드래그 이벤트 간섭 방지 (`e.stopPropagation()`) 적용
- [x] **TicketBoardView & Header 연동**
  - `Header`에 `onCreateClick` 이벤트 핸들러 바인딩
  - 최상위 View에서 모달 상태(`isOpen`) 및 CRUD 핸들러 바인딩 구조 완료

---

## 3. 次の作業手順
1. **DnD / `updateStatus` 動作確認**
   - ドラッグ＆ドロップ時の State 更新および API 呼び出しの確認
2. **作成 Modal / 削除 Dialog(Modal) の実装・連携完了**
   - API レスポンスの型変換処理を追加し、Modal 経由での CRUD テスト
3. **ブラウザ E2E 確認**
   - チケット作成 ➔ 編集 ➔ ドラッグ移動 ➔ 削除の全フローの動作確認
4. **`feature/ticket` 親ブランチへの最終統合**
   - Git Commit & Push 実行後、親ブランチへの PR 作成および Merge