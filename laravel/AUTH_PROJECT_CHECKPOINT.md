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

次の作業：

1. Ticket TypeとLaravel JSONの整合性修正
2. priority/status値の整合性確認
3. StoreのaddTicket payload確認
4. DnD/updateStatus確認
5. React Ticket tests追加判断
6. 作成Modal / 削除Dialog実装
7. ブラウザE2E確認
8. formatter / diff cleanup
9. Laravel / React全テスト
10. `git diff --check`
11. commit / push / branch整