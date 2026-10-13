# Ticket Project Creation — Child WORK

## 目的と責任
- Parent: `feature/ticket`; Child: `feature/ticket-project-creation`.
- 認証済みactive userによるProject作成、固定3文字key、変更されない`created_by`、初期leader/write登録を提供する。
- Project検索/UI、leader譲渡、archive/restore、削除権限拡張は対象外。

## 実装契約
- Fetch時点で最新Epicは`be3cb7b`。共通祖先`6e7614b`からEpic固有4 commits、Child固有9 commitsに分岐しているためfast-forwardでは統合できない。
- `POST /api/projects` はadmin以外のactive userも利用できる。作成・creator設定・作成者のleader/write登録をtransactionで行う。
- `created_by`はAPI入力で指定・変更できず、leader変更後も保持する。既存Projectは推測せず`null`を維持する。
- Project key衝突は最大5回まで再試行し、他のunique違反は再試行しない。
- `PATCH`/`DELETE`は従来どおりadmin限定。削除条件もEpic契約を維持する。
- Project Audit Child (`e723d79`) も`ProjectController::store`と`Project`のkey生成を変更する。統合ではProject、creator、leader/write、`project.created` audit insertを一つのtransactionにまとめ、Audit側の歴史的key予約とEpicの最大5回key衝突retryを両立させる。
- Lifecycle Child (`a52c78c`) はControllerの一覧・改名・削除に加えてarchive/restoreを追加し、Projectの`archived_at` castを持つ。Audit統合時はrename/deleteとarchive/restoreのイベント記録を各状態変更transactionに保つ。
- Leadership Child (`0d52402`) は`ProjectMemberController`でleader譲渡をlock付きtransactionにし、leaderのrole変更・削除を制限する。作成APIの初期leader/write登録をその唯一leader契約の入口として統合する。
- Discovery API Child (`31d9dc7`) はProjectControllerの検索・key lookupを変更する。Lifecycleのactive/archive filterと検索条件を同じ一覧queryで保持する。
- 本ChildのEpic比較差分は `docs/ticket/TICKET.md` の削除を含む。統合時は最新Epic Routerを保持し、この削除を適用しない。

## 検証状態 (SHA `67aa0cd58b96d3a58b74051f6d448bbf0cf10be6`)
- `ProjectManagementTest`: 12 tests / 61 assertions、Laravel全体: 115 / 513 が成功。
- Epic既存のevent injectionによるkey unique衝突・最大5回retryテストも成功。これは複数DB接続を使う実競合テストではない。
- `vendor/bin/pint --test` 成功。
- 専用SQLiteファイルDBで既存Project rowを作成後、Lifecycle `archived_at` (`000001`) → audit ledger (`000003`) → creator (`000004`) のschema-only overlayを適用。row保持とnullable列の`null`を確認。APIのlegacy null回帰テストも成功。Controller統合はしていない。
- 検証環境: Childごとに依存vendorとComposer autoloadを分離し、テスト用APP_KEYとSQLiteを指定。初回はvendor symlinkがEpic側のautoloadを参照し、APP_KEYも未設定だったためその結果を破棄して再実行した。migration helperも初回にDB環境変数を渡せず、明示設定で再実行した。既存`.env`・DBは使用していない。

## 未検証と統合ゲート
- MySQL migration、複数DB接続によるkey衝突、同時作成、transaction rollback fault injectionは未検証。
- 本Child単体にはaudit ledgerがない。SQLite overlayでmigration順と既存row互換性は確認済み。統合後はProject・creator・membership・audit eventの一括rollbackを回帰テストする。
- Discoveryのkey lookupとarchive済みProjectの可視性は未統合。Lifecycleの一覧filterは検索一覧に保持し、key lookupでarchive済みProjectを返す方針は別途確認する。
- 本Childは未merge。次はProject Audit Childとの`ProjectController`/`Project` 3-way比較および統合rollback回帰テスト。
