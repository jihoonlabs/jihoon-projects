# Ticket Board Usability Child

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-board-polish
role: child
status: validated-browser-pending
parent_branch: feature/ticket
base_sha: cd6ada3aafdcdd6d2e561e1180880e44a77be271

## Responsibility
既存のTicket操作画面を仕上げる。ログアウトの接続、Project背景色、重複詳細ボタンの整理、カードのダブルクリック、Project・権限の表示、コメントのレイアウトを対象とする。

## Boundary
API、データモデル、管理者・leader権限、Projectの作成・監査画面は変更しない。Project単位の既存ボードを維持する。

## Validation / Handoff
- 対象テスト37件、React全体26 files / 172 tests、TypeScript、ESLint、変更ファイルのPrettier、production buildは成功。
- ログアウトはserver成功後にsessionを消去し、失敗時は案内と再試行を提供する。送信中の重複要求を抑止する。
- タイトルクリックとカード余白のダブルクリックで詳細を開く。status選択は詳細操作と分離し、閉じた後のtitle focus復帰を維持する。
- Projectの不変keyから求める既存色をカード背景に適用する。Project切替と既存権限は維持し、コメントは改行・長文折返し・投稿日時を表示する。
- 未検証: 実browserの表示・pointer DnD・frontend→Laravelのログアウト。Chromium downloadが失敗し、Next serverも環境のnetworkInterfaces制限で起動できなかった。PHP/MySQL環境は存在しない。
- API・データモデル・権限は変更していない。コメント編集は本人、削除は本人またはadminという既存契約を維持する。leaderの権限拡張は含めない。
- アプリ検証SHA: `1dcaf449e949396caf5de89cb7fba78d64830f7b`。公開Git treeとローカルの検証済みファイルが一致することを確認した。Ticket V1全体の完了とは扱わない。
