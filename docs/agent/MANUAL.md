# AGENTS独立候補の比較資料

確認日: 2026-10-07（JST）。基準SHAと対象branchは [WORK](WORK.md) を参照。
本候補は文書だけを変更する。アプリの仕様変更やTicket統合、規則の正式採用は行っていない。

## 発見した問題と判断

| 根拠 | 問題 | 候補での対応 |
|---|---|---|
| v2の「複数の妥当案」「矛盾・不確実性」で確認、競合・文書矛盾で停止 | 普通の実装選択、古い記録、機械的な競合までユーザー待ちになる可能性 | 実装選択と調査は自律化。仕様・承認境界を決められない部分だけ確認 |
| v2のbranch/worktree禁止とdirty保護 | 安全な作業隔離まで承認待ちになり得る | 開発依頼に必要な独立branch/worktreeを許可。他者変更の保護と共有先への承認は維持 |
| 最新Epic `8a98235` のRouterはProjectアクセスを `feature/ticket-project-access` と記載、Child末尾は `feature/ticket-team-access` | Routerと引渡し先が食い違う | RouterにbranchとMD所在、統合commitを持たせる |
| 同Epicは順序保存・Projectアクセスを統合済み、同branchの両Child MDは統合未実施と記載 | 古い完了記録を現行状態と誤解する。順序保存MDの「Epicへmergeしない」意図にも実際の配置が一致しない | 現行状態は親Router、Child詳細は参照先で所有。完了MDは履歴として明示 |
| `b62d068` でAGENTSのmerge競合を統合branch側採用により解消 | 機能統合と全体規則の更新が同じdiffへ混ざる | 規則変更は独立候補に分離。意味の選択を伴うAGENTS競合は確認 |
| 統合MD `2877019` はテスト件数を記載するが検証対象コードSHAがない | branchが進んだ後、どのコードが通ったか判断しにくい | 引渡しと親の統合結果を固定SHA・コマンド・未検証事項に結び付ける |
| `ab24646` はコメントauthor.idの期待を文字列から数値へ修正。`9325dfc` は統合時の認証guardを修正。`3dabba0` はCSRF例外を削除し実ミドルウェアの回帰テストを追加 | Childの個別テストやmockの成功だけではAPI型・認証・実環境接続を保証できない | 親契約と接続点を確認し、統合後の最終コードで回帰検証 |
| v2のAGENTS改善節、WORKの優先事項・適用方針、MANUALの規則説明が重複 | 常時規則と候補の比較記録が混在。毎作業で最新調査まで始める可能性 | 常時の改善調査義務を削除。規則はAGENTS、再開状態はWORK、根拠はMANUAL |

上のコード・文書矛盾と競合は確認できた事実。停止回数、コンテキスト消費、速度への影響は測定しておらず、規則から推定したリスクとして扱う。v2のコードには順序保存が未実装でも最新Epicには存在するため、両branchの情報を混ぜない。

## 維持・削除・統合

- 維持: 責任単位、親Router、Child契約、統合後の回帰、他者変更保護、未検証の明示、規則採用の明示承認、日本語/既存英語。
- 削除: 全競合・全矛盾での停止、妥当案が複数あるだけでの確認、作業終了ごとの改善調査義務。
- 縮小: 小修正でのMD/MANUAL作成、MANUALへの実装・テスト詳細の重複、毎branchでの無差別な全検証。
- 補強: Childの基準/引渡しSHA、共有契約の所有者、履歴MDと現行Routerの区別、使い捨てDB、明示stageとpush先確認。

規則を短くするためにSHAや接続検証まで削ると、今回確認した統合問題を再現しやすい。一方、一般的なコーディング手順や固定テンプレート、全repo mapを常時読ませる効果は小さいと判断した。

## 外部資料と採否（2026-10-07取得）

- [OpenAI: Rethinking skills and prompts（2026-09-11）](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra): 条件付き読込と不要な承認境界の見直しを採用。特定モデルだけの能力を前提にテスト規則を全削除することはしない。
- [Codex: Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md): 適用される階層の指示確認を採用。32 KiBの上限まで規則を増やす目的には使わない。
- [Anthropic: Effective context engineering（2025-09-29）](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): 最小の必要情報と必要時検索、再開可能な短い状態記録を採用。全履歴の事前読込は不要と判断。
- [OpenAI: Using PLANS.md](https://developers.openai.com/cookbook/articles/codex_exec_plans): 完了条件まで継続し、長い作業の状態を更新する考え方を採用。初心者が全文だけで実行できる巨大な自己完結計画を全作業へ義務化しない。
- [astral-sh/uv AGENTS.md](https://github.com/astral-sh/uv/blob/main/AGENTS.md): 関連テスト優先と既存テスト重複の回避を参考にした。Rust固有の規則を移植しない。
- [agentsmd/agents.md AGENTS.md](https://github.com/agentsmd/agents.md/blob/main/AGENTS.md): repo固有の実行注意を短く置く例として参照。build禁止は同repoの開発server事情であり、こちらでは必要時の検証として残す。

外部資料は比較材料であり、常時読込の対象ではない。公開AGENTSは取得時の内容で、将来更新され得る。

## 確認結果と残る検証

3ファイルだけのdiff、相対リンク、競合マーカー、Git境界、Child引渡しと統合手順を確認。アプリコードを変更しないためアプリテストは未実行。過去のTicketテスト件数を今回の成功として扱わない。

本候補の運用効果は未検証。採用時は次の小修正とChild統合で、不要な確認が減るか、引渡しSHAと最終コードの検証が揃うか、親Routerが古いChild記録を現行と誤認させないかを確認する。失敗が確認された箇所だけ再調整し、固定の改善儀式は追加しない。
