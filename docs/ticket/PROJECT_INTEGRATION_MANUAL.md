# Project管理統合 — MANUAL

Projectの作成・保管・復元・監査履歴・リーダー管理・検索APIを、Ticket Epicへ戻す前に接続して検証するChildです。

## 統合した動作
- active userがProjectを作成すると、作成者がcreatorかつleader/writeとして登録され、作成監査記録も同時に保存されます。
- Projectの作成者情報は後から変更できません。Project削除後も監査記録とproject keyは残ります。
- 完了済みTicketだけのProjectをleaderが保管・復元できます。状態変更と監査イベントは同じtransactionで保存され、再要求で重複イベントを作りません。
- リーダー譲渡は既存のleaderが正確に1名の場合だけ成功し、権限変更とメンバー操作はProject row lock下で処理されます。
- Project検索は所属範囲を守り、通常一覧ではactive、`archived=1`では保管済みProjectを返します。名前/key検索と保管フィルターは同時に利用できます。

## 検証
- 実ブラウザーで一時SQLite DBを使い、Reactログイン、Project作成、creator/leader/write、rename、archive/restore、名前/key検索、archive filter、board selectorの表示を確認しました。
- DBで作成・rename・archive・restoreの監査イベントとsnapshotを確認しました。監査履歴UIはありません。
- SQLite in-memoryでLaravel 136 tests / 638 assertions、Pint、変更PHPのsyntax checkが成功しました。
- rollbackテストは作成監査・保管監査・復元監査の書き込み失敗時にProject状態と初期membershipが残らないことを確認します。
- migrationテストは既存Project行とkeyを保持し、legacyの`archived_at`と`created_by`がnullであることを確認します。

## 制約と状態
- 実行環境にMySQL/MariaDBがないため、MySQL migration、複数接続による作成競合・row lock動作は未検証です。
- この結果はIntegration Child内のローカル検証チェックポイントです。Epic/mainには未統合です。
