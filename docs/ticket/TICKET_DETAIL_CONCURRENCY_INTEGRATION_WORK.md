# Ticket Detail Concurrency Integration Candidate

owner_repo: jihoonlabs/jihoon-projects
owner_branch: integration/ticket-detail-concurrency-v1
role: integration_candidate
base_sha: 1d0af6114d2b354f64e4bc179a2eec94ce0c43a9
status: verified-not-adopted

## 入力と責任

- Parent/Epicは`feature/ticket`、実基準は上記base_sha。今回の承認は候補準備・検証・必要なローカルcommitまでで、Epic採用・main統合・push・既存資産削除は行わない。
- 適用Childは`feature/ticket-detail-concurrency`の`37a649666f1a45bff111a06c6d30b65da0a3df6f`。ChildのParent基準も上記base_shaで、独立test reviewと実接続を含むhandoffは完了している。
- 依存するUX Child `5c9c6e03a60b9b0ccba86e2d0915d2fbcbf0d99f`と採用候補`d260a70568d11272d8098e07ebc3f1a3370ae649`は既にParentの祖先に含まれる。追加cherry-pickせず、今回のChildだけを候補に一度fast-forward適用した。
- 既存の`integration/ticket-detail-first-ux-v1`は完了した別のUX責任・旧基準を所有し、`integration/ticket-epic`も今回の責任を所有しないため再利用しない。既存branch/worktree/ファイルを変更・削除していない。
- このWORKだけが今回の候補ownershipを持つ。Child WORK・MANUALとEpicの`TICKET.md`は既存入力として保持する。新機能は実装しない。

## 維持契約と確認する境界

既存show GET・権限・CSRFと最新詳細、Ticket version条件付きPATCHの200/409、競合入力保持と明示再取得、遅延応答破棄を確認する。既存詳細内編集/削除・担当者再編集・DnD/board_version・失敗復元を同じ候補の実APIで接続確認する。無条件の旧PATCHを維持し、その書き込みもversionを進める。

新migrationを既存Ticketデータがある専用一時SQLiteに適用して、データ保持とversion初期値を確認する。既存.env/DBとuntracked `ai/`は保護し、既存DBのreset・全体seedは行わない。

## 検証方針

- 候補のアプリコードとChild SHAの一致、依存の祖先関係、ownership/base SHAをGitで確認する。agent-guardがないため手動確認する。
- 専用の環境・DB・session・storage・cacheと候補自身のコードで実frontend→Laravel接続を確認。Childの証跡を今回の候補実行結果として流用しない。
- 関連Laravelの条件付き更新/Resource/順序/権限とReactの接続境界を確認し、最後にParent範囲のReact回帰を一度実施する。コード一致・変更なしの場合、Childで通過済みの全Laravel/type/lint/buildは理由なく反復しない。
- MySQLの別接続同時実行・isolation・row lockは未検証のまま。SQLite・要求順序制御を証明にしない。

## 今回の候補結果（Childの過去検証とは別実行）

- 検証したアプリコードSHA: `37a649666f1a45bff111a06c6d30b65da0a3df6f`。候補の`react/`・`laravel/`と依存manifest/lockはChildと一致する。接続・回帰修正SHAはなし。候補の追加commitはこの統合handoff文書だけで、最終候補SHAはowner_branchのHEADとする。
- 既存データへのmigration: 一時SQLiteに旧migrationまで適用し、限定fixtureの既存Ticket 5件を作成してからversion migrationを適用した。Ticketの全既存フィールド、users/projects/project_membersの全行は一致し、全Ticketのversionは1になった。既存DBのreset・全体seedは行っていない。
- 候補の実frontend→Laravel→一時SQLiteで既存UX/担当者/DnD/失敗復元9シナリオ成功。列内順序・列間状態の保存/reload、ドラッグ終了直後の詳細防止、同じ詳細の担当者再編集、実403後の復旧、失敗移動と並行した編集/作成/削除の成功保持、board_version 409の再取得/再試行、Project取得失敗時の元の案内保持を確認した。
- 最新取得と編集競合の接続7シナリオ成功。外部更新後のタイトル/詳細、2ブラウザー同一versionで先行200・後続409、入力保持と明示再取得/再編集、編集中の別クライアントのmove後の409と移動状態保持、実500/403/404、旧GET中断後の別Ticket表示を確認した。API応答mockなし。遅延はrequest deliveryだけを制御し、障害注入は専用一時DBだけで行った。
- 関連Laravel: `EditConcurrencyTest|ResourceContractTest|BoardOrderTest|ProjectAccessTest|CsrfProtectionTest`、23 tests / 162 assertions成功。
- integration-v1の最後のParent範囲React回帰を候補で一度実行: 24 files / 169 tests成功。遅延応答の逆転、遅延保存・競合再取得の成功/失敗も含む。
- Childで実施済みの全Laravel 144件/703 assertions、TypeScript・ESLint・Prettier・Pint・production build、独立test review（関連React 51件直接実行）は、同一アプリコードの既存証跡として区別して保持する。新たなコード変更・失敗・不確実性がないため今回繰り返していない。今回の確認を新しい独立test reviewと呼ばない。
- 既存.env・SQLite・`ai/`等の事前ハッシュ1612ファイルは変更なし。Parentは`feature/ticket` / base_shaのままでuntracked `ai/`を保持。Child、前の候補、previewも変更していない。
- 証跡と限定fixture/実行スクリプト: `/private/tmp/ticket-detail-concurrency-integration-check-20261012`。`migration-result.json`、`regression-result.json`、`freshness-result.json`、`laravel-tests.xml`、`summary.json`。候補ローカルの依存コピーを使い、専用のenv/storage/session/cacheとAPI 8130・frontend 3230で検証した。
- 今回、環境原因の未実行項目・未解決の実行後失敗はない。候補コードと適用Childの一致、文書参照、final diff/statusを確認した。

## 採用前の制約

現在のParent基準から候補はfast-forward採用可能で、SQLiteを使うローカル採用の阻害事項はない。採用自体とEpicの採用記録更新は未実施。新version migrationを起動前に適用する。既に含むUX・先行修正は重複適用しない。Parent HEADが変わった場合は差分と必要な再検証を先に確認する。

MySQL migration・別接続同時実行・isolation・row lockは未検証。SQLiteと要求順序制御から検証済みとは扱わない。keyboard DnDやTicket V1全体の完了は今回の責任に含めない。Epic/main統合、push、既存資産削除は行わない。

## Improvement note

今回の候補責任で新たな運用問題は確認されていない。
