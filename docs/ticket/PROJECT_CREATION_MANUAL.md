# Project Creation

ログイン中のactive userがProjectを作成でき、固定keyを持つProjectに作成者自身が最初のleader/writeメンバーとして登録されます。元の作成者IDは現在のleaderと独立して保存し、APIからの偽装・変更を拒みます。既存Projectの作成者は`null`のままです。

Project管理関連12 tests / 61 assertions、Laravel全115 tests / 513 assertions、Pintを確認済みです。schema-onlyの専用SQLite検証でLifecycle・audit・creator migrationを順に適用し、既存Project rowと`created_by = null`を維持しました。アプリコードを統合した検証ではありません。MySQL、実DB接続間の競合、transaction rollback fault injectionは未検証です。`PATCH`/`DELETE`の権限やProject UIはこのChildで変更していません。

Project AuditとのEpic統合は未実施です。Project・creator・初期membership・作成audit eventを一つのtransactionに収め、監査記録のkey予約とProject key衝突retryを維持する必要があります。詳細は `PROJECT_CREATION_WORK.md` を参照してください。
