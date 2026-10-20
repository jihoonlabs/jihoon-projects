# Ticket V1 開発・検証記録

## 文書の役割

このファイルは公開V1の実装範囲と、過去の検証記録をまとめる開発記録です。利用手順は [Ticket V1 マニュアル](README.md) から機能別ページを参照してください。AI向けの作業指示や次回作業の引き継ぎではありません。

## 公開V1の機能範囲

- 登録、ログイン、パスワード再設定を含むセッション認証
- プロジェクトの作成・一覧・検索・選択
- プロジェクトメンバーの追加、権限変更、リーダー引き継ぎ、削除
- 閲覧・編集権限に応じたプロジェクトとチケットの利用
- チケットの作成・詳細表示・編集・削除、ステータス変更、担当者設定
- チケットの検索、担当者フィルター、ドラッグ＆ドロップによる並び替え
- チケットコメントの閲覧・投稿・編集・削除
- プロジェクト終了・復元。終了時はデータを保持し、閲覧のみとする

## 実装上の前提

- Laravel APIとReact UIを分離し、APIのsnake_case応答をReactの画面モデルへ変換する。
- 認証はLaravel Sanctumのセッションを使う。認証、メンバー所属、閲覧・編集権限、コメント所有権はAPI側でも検証する。
- プロジェクトメンバーは「リーダー／メンバー」と「閲覧／編集」の権限を持つ。リーダーまたは管理者がメンバーを管理する。
- チケットの担当者は対象プロジェクトのメンバーに限る。
- チケットのステータスと列内 position はサーバーへ保存する。移動APIはボードバージョンを比較し、古い状態からの更新を競合として拒否する。
- プロジェクトの終了には、すべてのチケットが完了している必要がある。復元後に変更を再開できる。

## 設計とテストの具体例

### 1. 同時編集で他の利用者の変更を上書きしない

同じチケットを複数人が開いた場合、後から保存した古い画面の内容が先の変更を消す可能性があります。更新日時だけでは同じ秒の更新を区別できないため、チケットの整数 `version` とクライアントの `expected_version` を比較します。[TicketController](../../laravel/app/Http/Controllers/Tickets/TicketController.php) の更新SQLにバージョン条件と加算を含め、一致しない更新をHTTP 409として返します。並び替えはプロジェクト単位の `board_version` とトランザクションで整合性を扱います。

[EditConcurrencyTest](../../laravel/tests/Feature/Ticket/EditConcurrencyTest.php) では、時刻を固定した二人の編集、更新SQLのバージョン条件、並び替え後の古い編集、再取得後の編集を検証しています。競合時にタイトルや状態が上書きされないことまで確認します。

**制約:** 互換性のため `expected_version` を省略した更新も受け付けます。すべてのAPI利用者に楽観ロックを強制する設計ではありません。SQLiteでの回帰テストは、本番DBの物理的な同時実行・ロック待ちを保証しません。

### 2. 遅い応答が新しい画面状態を壊さない

一覧取得中に更新したりログアウトしたりすると、古い応答が後から到着します。[useTicketStore](../../react/src/features/tickets/store/useTicketStore.ts) は取得順序・変更リビジョン・認証セッションの世代を確認して状態への反映を制御します。同じチケットへの書き込みを順番に処理し、競合後は再取得します。セッション変更時は一覧を消去し、前のセッションに属する待機中の書き込みを実行しません。

[useTicketStore.test](../../react/src/features/tickets/store/test/useTicketStore.test.ts) では、更新と重なった古いGET、409後の再取得、ログアウト後の遅い一覧応答・削除失敗・待機中の更新を再現しています。単なる成功時の描画に加え、応答順序が逆転した場合の状態を確認します。

**制約:** UIの状態管理はサーバーの認可を代替しません。また、すでに送信されたHTTPリクエストをサーバー上で取り消す保証はありません。

これらは公開コードとテストから確認できる例です。AIの生成量や開発時間の削減率を示すものではありません。

## 自動検証と再実行

[Ticket CI](../../.github/workflows/ticket-ci.yml) はReact・Laravel・ワークフロー変更のPRと対象ブランチへのpushで実行します。実行結果は [Actions](https://github.com/jihoonlabs/jihoon-projects/actions/workflows/ticket-ci.yml) で対象コミットごとに確認できます。ワークフローの存在自体は成功を意味しません。

| 対象 | 環境 | 実行する確認 |
| --- | --- | --- |
| React | Node.js 24、pnpm 11.25.0 | lockfile固定インストール、Vitest、TypeScript、ESLint、production build |
| Laravel | PHP 8.3、Composer 2、SQLite | lockfileから依存を導入、テスト用アプリキー生成、PHPUnit |

ローカルでも同じ確認を実行できます。初回セットアップは [React README](../../react/README.md) と [Laravel README](../../laravel/README.md) を参照してください。

```bash
cd react
pnpm install --frozen-lockfile
pnpm test:run
pnpm exec tsc --noEmit
pnpm lint
pnpm build
```

```bash
cd laravel
composer install --no-interaction --prefer-dist
composer test
```

CIでは外部OAuth、メール配送、ブラウザーE2E、本番DBの負荷・同時実行は確認しません。ビルド時のGoogle Fonts取得にはネットワーク接続が必要です。

## 既知の制約

- メンバー追加は登録済みユーザーのメールアドレスを指定する方式で、アプリ内の全利用者検索・招待フローはありません。
- この記録は公開V1の範囲を示すもので、Jira相当の全機能や本番運用適合性を意味しません。
- 詳細な未着手作業、内部AI引き継ぎ、運用上のノウハウは非公開の作業文書で管理します。

## 検証記録

2026-10-18のプロジェクト一覧ダイアログ改善では、React 248 tests、TypeScript、ESLint、production buildを通過しました。変更のないバックエンドは同一ソースの隔離環境でLaravel 158 tests、1,624 assertionsを再確認しました。

Chrome HeadlessとローカルAPIで、ログイン、一覧の開閉、Escapeとフォーカス復帰、プロジェクト選択・作成、幅390pxでの表示を確認しました。メールの実配送、外部OAuth、本番環境はこの確認に含みません。

以前のTicketチェックポイントでは、次を通過したと記録されています。

- Laravel: 85 tests、361 assertions
- React: 112 tests
- TypeScript、ESLint、Pint、production build
- Chrome Headlessでログイン後のTicketとコメントの主要CRUDフロー

上の過去チェックポイントの数値は当時の履歴です。現在のコード全体やすべての環境での動作保証として扱わず、対象ブランチのCIとテスト結果を確認してください。

## 関連資料

- [機能別利用マニュアル](README.md)
- [認証](manual/authentication-v1.md)
- [プロジェクトとメンバー](manual/projects-v1.md)
- [チケットボード](manual/tickets-v1.md)
- [コメント](manual/comments-v1.md)
