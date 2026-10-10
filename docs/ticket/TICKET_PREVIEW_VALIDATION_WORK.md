# Ticket preview 検証・回帰修正

## 目的と状態
- Worktree: `/private/tmp/ticket-preview-worktree`、Branch: `ticket-preview`、基準SHA: `7504cb5a1ec7744ce2ad178518b46d5ab7f0c217`。
- 添付相当の `/Users/parkjihoon/Downloads/ticket-preview-20261010.patch` を重複・衝突確認後に適用。patch記載の未公開commit `ce546636344aa76dd14a11c787e6a20c8f733e94` はfetchせず、作業開始HEADも変更していない。
- `feature/ticket` の別worktreeとその `ai/`、既存 `.env`、保存DBを変更していない。ブラウザー用データは新規の `/private/tmp/ticket-preview-browser-20261010-final.sqlite` のみ。

## 変更内容
- DnD失敗時にProject全体の古いsnapshotへ戻すと、同じProjectの成功した編集・作成・削除まで失われる。回帰テストで再現し、現在の配列内で変更されていない楽観更新だけを戻すよう修正した。移動対象Ticketは同一Ticketのwrite queueで保護する。
- 手動status変更のrejectを画面側で捕捉し、既存alertに表示する。未処理Promiseを残さない。
- 開始時のReact失敗13件の内訳は、rejectするstore APIに対して成功扱いでawaitしていた5件と、全Project初期表示後もProject選択を省略していたBoardテスト8件。現在の契約に合わせたテスト修正と回帰ケース追加後、全件pass。

## 実行した検証
- Node `v24.2.0` / pnpm `10.19.0`、lockfile固定の依存をinstall。manifest/lockfile差分なし。
- React `pnpm test:run`: 23 files / 140 tests passed。
- `pnpm exec tsc --noEmit`, `pnpm lint`, `pnpm build`: passed。buildはsandbox内でGoogle Fonts取得が拒否されたが、同じコマンドをネットワーク許可で再実行して成功。
- PHP `8.5.5` / Laravel `13.7.0`、`php artisan test`: 136 tests / 638 assertions passed。`phpunit.xml` のメモリSQLiteを使用。`./vendor/bin/pint --test`: passed。
- ブラウザー用の別ファイルSQLiteにmigrationを実行し、仮アカウントでChrome `155.0.8059.39` を使用。既存DBへmigration/reset/seedingしていない。
- 実ブラウザー: ログイン、全Project/個別Project切替、read権限の詳細表示と編集不可、編集成功、保存失敗後の入力保持と同一Ticket再保存を確認。
- 実ブラウザー: 手動status PATCHを失敗させた後にTODOへrollback、alert表示、未処理Promise 0件を確認し、再試行でDONEになった。
- 実ブラウザー: 同じ列の順序 `Order Second → Order First` がreload後も維持され、列間移動もreload後に維持された。
- 実ブラウザー: 古い `board_version` のPATCHが409となり、board再取得後の次のDnDが成功。
- 実ブラウザー: DnD要求と続くTicket一覧再取得をそれぞれ失敗させた状況で、別Ticketの編集・作成結果保持と削除状態保持を確認。各操作で再取得失敗を個別に発生させた。
- CSRFの初回ログイン失敗はテストサーバーの誤った `SESSION_PATH` 指定が原因。Network上でCSRF応答204とCookieを確認し、Cookie Pathを `/` に直すと `XSRF-TOKEN` が利用可能になりログイン成功。アプリのCORS/API契約は変更していない。
- `git diff --check`: passed。最終HEADは基準SHAのまま。

## 未検証・残る制約
- `pdo_mysql` PHP拡張はあるが、この環境にMySQL client/serverや専用テスト接続先がない。MySQL migration、独立接続間の実競争、row lockは未実行。
- 詳細モーダルはBoardのTicket snapshotで開き、個別GETによる最新データ再取得はしない。編集version競合検知もないため、他利用者の同時編集を保護しない。今回の範囲では仕様追加を避け、変更していない。
- Ticket詳細のissue key/日時表示とmodalのEscape・focus trapは未実装。
- 実行中の一時サーバーは停止済み。今回のローカル検証チェックポイントはcommit対象。公開push、Epic/main merge、AGENTS変更は行わない。

## 次の作業候補（未着手）
- カードから詳細を開き、編集・削除は詳細画面内から行う。
- ボタン・モーダル・カードのデザインを整理する。
- タイトル領域に淡いProject背景色を使う案を検討する。
- Project色を保存・維持し、完全一致する色値の重複を防ぐ。同系色は許可する。

Ticket V1全体は未完了。上記候補の実装は開始していない。
