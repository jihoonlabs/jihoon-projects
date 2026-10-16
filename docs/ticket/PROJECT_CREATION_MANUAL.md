# Project Creation

ログイン中のactive userがProjectを作成でき、固定keyを持つProjectに作成者自身が最初のleader/writeメンバーとして登録されます。元の作成者IDは現在のleaderと独立して保存し、APIからの偽装・変更を拒みます。既存Projectの作成者は`null`のままです。

## 全プロジェクトからの作成（2026-10-16）
- ボードの「＋プロジェクト作成」は既存の作成フォームを開き、Project名へフォーカスします。「＋チケット作成」は全体表示でも利用でき、フォーム内で作成先Projectを選びます。
- 選択先のメンバー・権限を取得してから保存可能になります。Project変更時もタイトル・説明は保持し、別Projectの担当者を誤送信しないよう担当者のみ解除します。閲覧権限のみの場合は保存できず、取得失敗はフォーム内で再試行できます。APIの権限検査は変更していません。
- 保存中はProject選択を含む入力を固定し、失敗時は下書きを保持します。全体ボードの編集・状態変更・ドラッグは引き続き個別Project選択後に行います。
- React233 tests、type、ESLint、Prettier、production buildが通過。実Chrome→Laravel→専用MySQLでProject生成、admin/write memberのTicket生成、保存409後の明示再試行201、read memberの403、Project/担当者、reload、desktop/mobileを確認しました。
- `feature/ticket-acceptance-v1`で検証済み。今回のLaravelコード・DB schema変更はなく、元のDB/.envは保全しています。Epic/main未採用、利用者の確認は継続中です。大規模負荷・今回の独立reviewは未実行です。

## 初回API Childで実施した検証（過去の範囲）

Project管理関連12 tests / 61 assertions、Laravel全115 tests / 513 assertions、Pintを確認済みです。schema-onlyの専用SQLite検証でLifecycle・audit・creator migrationを順に適用し、既存Project rowと`created_by = null`を維持しました。アプリコードを統合した検証ではありません。MySQL、実DB接続間の競合、transaction rollback fault injectionは未検証です。`PATCH`/`DELETE`の権限やProject UIはこのChildで変更していません。

Project AuditとのEpic統合は未実施です。Project・creator・初期membership・作成audit eventを一つのtransactionに収め、監査記録のkey予約とProject key衝突retryを維持する必要があります。詳細は `PROJECT_CREATION_WORK.md` を参照してください。
