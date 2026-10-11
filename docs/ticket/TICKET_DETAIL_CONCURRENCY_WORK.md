# Ticket Detail Freshness and Edit Concurrency

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-detail-concurrency
role: child
base_sha: 1d0af6114d2b354f64e4bc179a2eec94ce0c43a9
status: ready_for_integration

## 責任と境界

タイトル・詳細ボタンから最新Ticketを取得し、取得中・失敗・削除・アクセス権限喪失を区別する。編集の基準バージョンを保存時に原子的に比較し、競合時は入力を保持する。画面切替・終了後の遅延応答は破棄する。

完了済みUX Childの責任は拡張しない。色・Activity・新デザイン、Epic/mainへの統合、push、既存資産の削除は対象外。Epicの既存untracked `ai/`、環境設定・DB、他の作業空間を保護する。親への採用は別作業であり、Ticket V1全体は未完了。

## 契約と統合前提

- 既存GET `/api/tickets/{id}`を`no-store`で利用し、取得成功まではカードの古い情報・編集操作を表示しない。Ticket idごとの画面、AbortControllerとactive/aliveガードで古い応答を破棄する。
- 追加migration `2026_10_11_000000_add_version_to_tickets_table.php`でTicketに正の単調増加`version`を導入する。`updated_at`やProjectの`board_version`を編集の比較値として流用しない。
- PATCHの任意`expected_version`は`WHERE id AND version`と`version + 1`を同一SQLで実行する。不一致は409 + `code: ticket_conflict`。競合時は並び順・Projectのboard_versionも変更しない。
- 既存の無条件PATCH・手動ステータス変更・DnD API契約は維持する。これらの書き込みと実際に変更されたpositionもTicket versionを進める。無条件の旧クライアント自身の競合防止までは保証しない。
- Projectの既存transaction/lock規律を維持し、PATCH応答のフィールド・versionはtransaction内で固定した保存スナップショットを返す。クライアントもそのフィールドとversionを一緒に採用する。
- 競合中の再取得は入力・保存基準を変えない。最新内容を別表示し、保存は無効のまま。「最新情報で編集し直す（入力を置き換える）」という明示操作だけが入力と基準を更新する。自動上書き・自動再試行は行わない。
- 成功した保存と後続のProjectメタデータ取得失敗を区別する。担当者再編集・DnDの失敗復元は既存契約を維持する。

## 今回の検証（以前のUX検証とは別実行）

- React全体: 24 files / 169 tests成功。TypeScript、ESLint、変更ファイルのPrettier、production build成功。
- Laravel全体: 144 tests / 703 assertions成功。version条件の単一SQL、同時刻の2編集者、競合時の順序・board_version保持、旧PATCH・DnD互換、担当者、403/404/422を検証。Pint・diff check成功。
- 保存応答の境界: Laravel transaction終了イベントと応答直列化の間に、同一接続で後続変更を注入する決定的テストを追加。物理commit・ロック解放・別接続の同時実行を検証したものではない。
- 独立test review: `/root/detail_concurrency_test_review`が読取専用で検討。応答の新versionと古い入力の組合せによる上書きの可能性を発見し、サーバーのスナップショット固定とクライアントの同時採用で修正。遅延保存/競合再取得の成功・失敗、Ticket切替、API契約を補強し、独立実行2 files / 51 tests成功。再レビューに阻害事項なし。追加Laravel境界テストの限界も独立確認済み。
- 実接続は責任専用 `/private/tmp/ticket-detail-concurrency-check-20261011` の一時SQLite・env・storage・session・cacheで実行。既存.env/DBは変更しない。API応答mockなし。
- Chromeで既存回帰9シナリオ成功: タイトル/詳細、担当者再編集、列内・列間ドラッグ、reload後の保存維持、ドラッグ直後の詳細防止、権限、手動状態変更、編集/削除失敗復旧、失敗移動と並行した成功の編集/作成/削除保持、stale boardとProject取得失敗。
- 新しい実接続6シナリオ成功: 外部変更後のタイトル/詳細からの最新取得、2ブラウザー同一versionでの最初の200・後続409、入力保持と明示再取得/再編集、実Laravelの500と再試行、会員権限喪失403、外部削除404、遅延GET中の閉じる/別Ticket表示。API応答の差替えは行わず、通信遅延はrequest deliveryの制御だけで再現した。
- ブラウザーの切替では旧GETの中断を確認。中断が無視されて応答が逆転する場合、および遅延保存/競合再取得の成功・失敗はReact deferredテストで検証した。
- 証跡: `/private/tmp/ticket-detail-concurrency-check-20261011/{regression-result.json,freshness-result.json,laravel-tests.xml}`。`regression.cjs`、`freshness.cjs`、`setup.py`、`run.py`と専用toolsを同じ場所に保存した。Childの既存環境ファイルのハッシュは保持。
- 最終Childはowner_branchのHEADとして引き渡す。採用前に新migrationを適用し、この責任とUX Childを重複適用しない。Epic基準は上記base_shaのまま。

## 実行失敗と未検証

- production buildの初回はsandboxのGoogle Fonts通信制限で失敗。許可されたネットワークで再実行し成功。
- 追加Chrome検証の初回は共有一時Playwrightのファイル欠損で未起動。別の責任専用toolsへ復旧した。実行後のハーネス内Response.status参照と説明入力選択子の失敗を修正し、6シナリオすべて再実行して成功。これらはハーネスの実行失敗であり、残るアプリケーション検証失敗はない。
- MySQLの別接続同時実行・isolation・row lockは未検証。SQLite結果やSQL条件の確認で検証済みとは扱わない。
- 今回の承認範囲で環境原因の未実行シナリオ・未解決の実行後失敗はない。Epic採用・隔離統合は未実施。

## Improvement note

共有一時Playwrightの欠損で追加検証が開始できなかった。責任専用toolsに復旧し、検証開始前にモジュールの解決を確認する。
