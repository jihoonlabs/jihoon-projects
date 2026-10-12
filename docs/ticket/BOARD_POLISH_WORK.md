# Ticket Board Usability Child

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-project-entry
role: child
status: validated-browser-pending
parent_branch: feature/ticket
base_sha: ed67f6edbaa8369ef7059ec6fe43f9ee91a19350

## Responsibility
既存のProject APIを一覧・作成画面につなぎ、Projectがない利用者も作成からTicket運用を始められるようにする。Ticket作成成功後のProject再取得失敗も保存失敗と混同しない。

## Boundary
Backend API、データモデル、管理者・leader権限を変更しない。既存のactive userによるProject作成契約を使う。rename/archive/restore・監査画面は対象外。Project単位の既存ボードを維持する。

## Current validation / Handoff
- React全体27 files / 180 tests、TypeScript、ESLint、変更ファイルのPrettier、production buildは成功。
- CSRF付きのProject作成、初期一覧取得中の作成抑止、二重送信防止、失敗時の入力保持・再試行、名前/key検索、選択を確認した。
- Projectがない一般利用者が作成し、serverのleader/write membershipを取得してメンバー管理・Ticket作成画面へ進めることを確認した。ProjectがないadminにもTicket作成を表示しない。
- Ticket保存成功後のProject GET失敗は保存失敗として扱わず、一覧エラーを表示して作成画面を閉じる。
- API・権限・DB schemaは変更なし。単独Childのため、親基準との差分に全React回帰を実行した。
- 未検証: 実browserの見た目・pointer DnD、frontend→Laravel→DBの実接続、MySQL。今回は既知の環境制限を理由に同じbrowser installを反復していない。
- アプリ検証SHA: `79f2a8e36012621e5fb6150703263459c435ac21`。公開Git treeと検証済みローカルファイルの一致を確認した。社内基本機能と利用者指摘の修正を満たすまではV1完了と扱わない。

## Previous adopted validation / Handoff
- 対象テスト37件、React全体26 files / 172 tests、TypeScript、ESLint、変更ファイルのPrettier、production buildは成功。
- ログアウトはserver成功後にsessionを消去し、失敗時は案内と再試行を提供する。送信中の重複要求を抑止する。
- タイトルクリックとカード余白のダブルクリックで詳細を開く。status選択は詳細操作と分離し、閉じた後のtitle focus復帰を維持する。
- Projectの不変keyから求める既存色をカード背景に適用する。Project切替と既存権限は維持し、コメントは改行・長文折返し・投稿日時を表示する。
- 未検証: 実browserの表示・pointer DnD・frontend→Laravelのログアウト。Chromium downloadが失敗し、Next serverも環境のnetworkInterfaces制限で起動できなかった。PHP/MySQL環境は存在しない。
- API・データモデル・権限は変更していない。コメント編集は本人、削除は本人またはadminという既存契約を維持する。leaderの権限拡張は含めない。
- アプリ検証SHA: `1dcaf449e949396caf5de89cb7fba78d64830f7b`。公開Git treeとローカルの検証済みファイルが一致することを確認した。Ticket V1全体の完了とは扱わない。
