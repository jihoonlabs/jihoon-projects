# Ticket main統合準備

## 目的・境界
- リモートGitだけを基準に、Ticket Epicを最新mainへ統合する前の差分・接続・回帰を確認する。
- 自宅Macのファイル、DB、Chrome sessionは使用しない。main merge/push、既存ブランチ削除、新仕様、AGENTS.md変更は対象外。

## 確認したrefs (2026-10-08 JST)
- main: `59b27f297f0b8d784f6f712ff4109721492adaf1`
- Epic: `f18cfd70aac6e3cebf2db2752ad7f615aaa4e929`
- 採用Project key Child: `2ab0ea4e2a64fa7207de799669aeab7b03574935`。Epicの祖先であることを確認。
- 共通祖先: `53b268d4d8b3f2b5559ba4aef317f1ebe9a50757`。main側20、Epic側102の独立commitがある。

## 統合範囲と判定
- `git merge-tree --write-tree origin/main origin/feature/ticket` は競合なし。これはGit objectのシミュレーションであり、ブランチをmergeしていない。
- シミュレーションtree: `9b7f1676f506165748ec981ef159e2cdc282fcc3`。
- このtreeとmainの差分は74 files / 2816 insertions / 254 deletions。Ticket文書、LaravelのProject権限・採番・board順序・migration・テスト、ReactのProject連携・カード・store・テストを含む。
- このtreeとEpicの差分はmain側の `docs/agent/WORK.md` と `docs/agent/MANUAL.md` の追加だけ。Laravel/ReactはEpicと同一、AGENTS.mdとagent文書はmainと同一。コードの再検証はEpic SHAで実行した。
- コード修正は不要。今回の追加変更は統合準備の文書だけであり、上記treeとdiff数には含まない。

## 今回実行した検証
- 新しいリモートcheckoutに `pnpm install --frozen-lockfile` と `composer install` で依存を導入。lockfileは変更していない。
- Laravel: PHP 8.4.26、全109 tests / 487 assertions成功。既存データbackfill・Project採番・seed再実行・削除後の番号非再利用・権限・board回帰を含む。
- Pint: 全体 `--test` 成功。mainとの差分に含まれるPHP 41ファイルのsyntax checkも成功。
- SQLite: 新しい一時DBで全20 migration、TicketSeeder、再seedが成功。再seed前後でProject key、next_ticket_number、既存Ticketのissue_keyが同一であることを比較確認。
- React: 全22 files / 129 tests、`tsc --noEmit`、ESLint、production build成功。
- `git diff --check` 成功。確認時のEpic HEADにGitHub Actions runはなし。CIの成功を今回の証拠として扱わない。

## 過去の検証・今回の未検証
- 過去: Child/EpicでLaravel 109 tests / 487 assertions、React 129 testsと各品質チェックが成功。Child SHAでChromeによるProject key独立、連番、名前変更後のkey維持を確認。V1のブラウザー回帰記録は `ticket-v1-integration.md` を参照。
- 今回は実ブラウザー検証を再実行していない。今回のUI検証はReactテストとbuild。
- MySQL migrationは未検証。MySQL 8.0.46 binaryを一時環境に準備しデータ領域を初期化したが、実行環境がUnix socket作成を許可せず、server startupが失敗した。migrationは実行していない。
- composer.jsonのPHP制約は `^8.3` だが、現在のcomposer.lockにはPHP >=8.4を要求するSymfony 8が含まれる。PHP 8.3でのinstallは失敗し、8.4で同じlockfileのinstall・テストが成功。これはmainにもある既存の依存条件で、今回変更していない。

## 再開・完了条件
- 状態: Git統合準備と可能なリモート回帰検証は完了。main統合は未実行。
- 承認後、最新refsをfetchし上記SHAから動いていないか確認する。変更があれば差分と必要な検証を更新する。
- main統合時も最新mainのAGENTS.mdとagent文書、採用済みChildの権限・board version・採番契約を保持する。
- MySQL利用環境へ適用する前に、利用予定のMySQL版で既存データmigration/backfillを確認する。ブランチ削除は別途承認後に扱う。
