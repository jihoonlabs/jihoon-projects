# AGENTS改善 WORK

## Version
v2.1 review candidate — `review/agents-v2-1-codex-20261007`

## Goal
`docs/agents-v2` のv2.1を基準に、分業・逆順統合の安全性を保ちつつ、不要な停止と常時読み込む規則を減らす。通常作業の全工程にこの改善文書を読ませない。

## Basis
- Base: `be26cb1300ba274370513226c4ac53cf4bd1e610`
- 対象: `AGENTS.md`, `docs/agent/WORK.md`, `docs/agent/MANUAL.md`
- 実作業ではTicket Child単体の成功後、親統合でAPI・認証・UI境界の修正が必要だった。Routerのbranch名とChildの記録が食い違う例もあった。
- 特定AIやIDEの能力に依存せず、Gitの固定SHAと短いMDで環境間を引き継ぐ。

## Decisions
- 依頼に含まれるAPI・UX・データ変更まで再確認しない。未確定の仕様選択、範囲拡大、不可逆操作を確認境界とする。
- 小修正ではChild・専用MD・MANUALを必須にしない。必要な作業文書をRouter/Child/ユーザー報告に分け、同じ事実を複製しない。
- Parent RouterにChildのbranch/MD所在、共有契約、状態、採用SHAを置く。Childは検証したSHAと実施結果に加え、未検証事項・残る制約を引き継ぐ。
- 分解は上位→下位、統合は検証済み下位→上位。親の最終コードで接続点と回帰を検証する。
- テストは近い範囲から始め、変更の影響に応じて拡大する。機械的な全件再実行を要求しない。

## Validation and application
- 3文書の差分・整合性・Git上の変更範囲を確認する。文書のみのためアプリテストは実行しない。
- この候補は正式採用前。進行中のTicket作業へ遡及適用しない。
