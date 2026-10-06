# AGENTS独立候補 — 統合と自律判断

作成日: 2026-10-07。原本と比較対象の固定refはWORKを参照。
他AIのreview候補は読まず、原本v2から判断した。アプリコードは変更していない。

## 現行構造で確認した問題

| 確認した事実 | 問題と候補の対応 |
|---|---|
| 原本v2は不確実性や複数の妥当案がある判断を確認対象にしている | 通常の実装方法まで確認待ちになり得る。公開仕様・権限・データ・依存・大きな構成の変更に境界を絞る |
| 原本v2は文書矛盾・想定外Git状態を一律停止対象にしている | 古い履歴や無関係なdirtyでも停止し得る。証拠で解ける状態記録の差異は整理し、仕様矛盾や変更重複だけ止める |
| 原本のTicket Epicは順序永続化を未実装としているが、Ticket統合refではposition/board_versionとmove APIが実装済み | ブランチの違いを文書誤りと混同しない。開始HEADと検証対象refを記録する |
| 統合refのTICKET.mdはChildを統合済みとする一方、TICKET_ORDER_PERSISTENCE.mdは未統合と記録。Child文書には「Epicへmergeしない」とあるが統合refに存在する | Child単独完了の記録と親統合の記録が混在する。親は採用SHAと統合状態だけ所有し、詳細は担当MDへ参照する |
| 同refのRouterはProject Accessをfeature/ticket-project-accessと記載し、TICKET_TEAM_ACCESS.mdはfeature/ticket-team-accessと記載 | 誤ったrefを統合する危険。実際の送先・採用SHA・MDパスを確認する。今回ブランチ名の正誤は断定しない |
| ticket-v1-integration.mdはカードのaria-disabledが手動状態変更/readの詳細操作にも影響した回帰と修正を記録。Card/index.tsxでaria-disabled解除を確認 | AccessとOrderの単独成功では接続点の保証にならない。統合HEADでフィルター×手動操作、read×詳細/コメントの実操作を確認する |
| Laravel phpunit.xmlは一時SQLiteを指定、React package.jsonはtest:run/lint/buildを提供。原本treeには.github/workflowsがない | 検証入口はあるが、毎回全検証では非効率。反復は対象テスト、完了・統合時は影響範囲の回帰。CIの常時保証は想定しない |

上記の停止リスクは規約の読解による判断であり、全てが実行ログで再現した事象ではない。
Ticketの検証成功数は文書上の過去結果であり、今回再実行した結果ではない。

## 残す・削る・変える

- 残す: 1 Child = 1責任、薄いEpic Router、既存変更保護、承認されたGit操作、統合後回帰、事実に基づく報告、日本語方針。
- 削る: 常時のMANUAL更新、全作業ごとのルール改善チェック、単なる実装上の複数案に対する確認要求、無条件の全作業停止。
- 統合する: 検証済み/未検証/未完成の重複指示は検証記録と報告の項目へ集約。AGENTSは不変の境界、作業MDは現在の状態、MANUALは説明/比較根拠を所有する。
- 明確にする: 依存の調査は自律、仕様変更は確認。調査範囲の拡大と作業範囲の拡大を区別する。停止は影響する変更だけに限定する。
- 補う: 送先HEAD/Child SHA、依存順、接続点の検証、検証証拠の対象SHA、staged diff、リモートSHA、一時DBの接続先確認。
- 新しい仕組みは作らない: CI、スキーマ生成、並列agent、worktree、自動承認機構は今回導入しない。文書は権限制御を技術的に強制するものではない。

## 比較した一次資料

参照日: 2026-10-07。公開例は更新され得る。以下は比較資料であり日常作業の必読文書ではない。

- [OpenAI: Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
  必要時の文書読込み、明確な完了条件、自律実行できる安全範囲を採用。モデル固有の慎重さを理由にGit保護や検証を撤廃しない。
- [OpenAI: AGENTS.md discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
  ルートから下位ディレクトリの指示を適用する仕組みを踏まえ、「全AI作業に優先」という絶対表現を削除。WORK/MANUALが自動読込みされるとは仮定しない。階層文書の増設は現状の規模では不要と判断。
- [Anthropic: Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  パス/refを保持し必要時に取得する方式を採用。固定ファイル数への制限も全体の事前読込みも避ける。multi-agent等の追加構成はそのまま採用しない。
- [astral-sh/ruff: AGENTS.md](https://github.com/astral-sh/ruff/blob/main/AGENTS.md)
  実際の変更、関連テスト、対象ファイルへの検証を重視する点を採用。Rust固有ルールやsnapshot自動更新設定は移植しない。
- [vercel/next.js: AGENTS.md](https://github.com/vercel/next.js/blob/canary/AGENTS.md)
  目的別のテスト/build選択、ログを再利用して不要再実行を避ける点を採用。巨大なframework開発の全README必読・全bootstrap buildはこのアプリへ移植しない。
- openai/codexのAGENTS.mdも取得を試みたが404/取得エラーのため根拠には用いていない。

## 検証と採用

今回の変更は3文書のみ。原本との差分、空白、参照先、承認境界、作業MDとMANUALの重複、下記シナリオを机上確認した。アプリの自動テスト・ブラウザー回帰は対象外で未実行。

| ケース | 候補での判断 |
|---|---|
| 無関係な個人AIファイルがdirty | 保護して継続。checkoutで上書きされるなら停止。無断stashしない |
| API利用側の関連コードが当初指定外 | 読取りは自律。承認仕様を満たす付随修正は継続 |
| EpicとChildの過去の統合状態が違う | ref/SHAで整理。権限仕様自体が違うなら確認 |
| Childテスト成功、統合後read操作が失敗 | 既存仕様内の回帰を修正し、接続点と関連回帰を再検証 |
| ブラウザーやOllamaが利用不可 | 未検証を明記し、利用可能な自動検証を続ける。完了と偽らない |
| ユーザーがcommit/pushまで承認済み | 指定ブランチへ実行しSHA確認。main merge承認とは扱わない |

これは独立候補であり最終採用前。AGENTS本体の削減量と文書確認結果はWORKを参照。
実運用での質問回数・誤統合・検証漏れの改善効果は未測定。採用判断はユーザーが他候補と比較して行う。
