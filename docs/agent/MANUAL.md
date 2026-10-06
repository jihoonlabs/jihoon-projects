# AGENTS独立候補 更新報告

確認日: 2026-10-07。基準: `docs/agents-v2` @ `66a70de5ba5a68605b26695d2d568cb2d64ea68a`。
他AIのreview候補は読まず、原本と実作業・公開資料から独立して作成した。採用・main統合・既存作業への反映は行っていない。

## 実際の構造と問題

WebはLaravel APIとNext.js UI、PHPUnit/Vitestの双方を持つ。基準branchには `docs/ticket/TICKET.md` があり、最新Ticket親はRouter、個人AI親は多数のChild結果を保持する。WORK/MANUAL分離はv2の方針であり、全プロジェクトで既に運用済みとは扱わない。

| 確認できた事実 | 問題と候補への反映 |
|---|---|
| Ticket統合記録はAGENTS競合を親側基準で解消したと記載する。[統合記録](https://github.com/jihoonlabs/jihoon-projects/blob/28770195e96a0a504dd2d40c85a044dff5fe1502/docs/ticket/ticket-order-persistence-integration.md) | 古いChildが共有ルールを持ち帰る。共有担当と親ルール保持を明記し、一括ours/theirsは避ける。 |
| 最新Ticket Routerは順序永続化を統合済みとするが、取り込まれたChild MDは未統合・次にfast-forwardすると記載する。RouterのProjectアクセスbranch名も実Child文書のteam-accessと一致しない。[親](https://github.com/jihoonlabs/jihoon-projects/blob/8a9823503b91f79590653b400111bac0adc6f1dd/docs/ticket/TICKET.md)・[Child](https://github.com/jihoonlabs/jihoon-projects/blob/28770195e96a0a504dd2d40c85a044dff5fe1502/docs/ticket/TICKET_TEAM_ACCESS.md) | 文書が現在状態と当時の記録を混在させる。親は統合SHAと結果、Child詳細は固定参照で区別する。過去記述の訂正だけで停止しない。 |
| 統合記録はLaravel46件・React128件のPASSを記載するが実行commandと環境はない。ブラウザー確認の実績も記載されていない。 | 件数だけでは検証範囲・再現性を判断しにくい。対象コード、command、結果、環境、未検証を対応させ、Childの実ブラウザー結果を統合後へ流用しない。 |
| 個人AI Epicは11,518 bytesで、Childごとの実装・検証を継続追記する。Childは同じcheckout、worktree禁止、限定コンテキストを指定する。[Epic](https://github.com/jihoonlabs/jihoon-projects/blob/425087ef7d246d529e3522d198175c7e4691e500/docs/personal-game-ai/EPIC.md) | Routerが履歴集になる。親は参照中心にする。ただし既存ツールの入力制限やworktree禁止をAGENTS変更だけで解除しない。 |

以下は発生した事故の断定ではなく、原本規則から判断した運用リスクである。
- 「複数の妥当案」「不確実性」「文書との矛盾」で停止すると、通常の実装選択や古いMDでもユーザー待ちになる。
- 「想定外のGit状態」で全面停止すると、無関係なdirtyを保全したまま進める作業まで止まる。
- 毎回の改善調査とWORK/MANUALの一律運用は、本来の変更より文書処理を増やす。

## 維持・削除・変更の判断

- **維持:** 責任ごとのChild、親Router、必要時の探索、親での接続・回帰検証、他者変更の保全、AGENTS変更の明示依頼、Web文書の言語方針。
- **削除・縮小:** 毎作業後のAGENTS改善研究、複数案だけでの質問、文書不一致や無関係dirtyでの全面停止、小修正の文書新設、常設ルール内の反復説明。
- **補強:** Childの基準SHAと共有担当、検証済みSHAの統合、親進行時の再確認、検証結果とコードの対応。新しいツール・承認段階・分業階層は追加しない。
- **WORK/MANUAL:** WORKはこの候補の再開情報、MANUALは比較根拠と実績。互いに規則を再定義せず、通常作業にこの報告の読込を要求しない。

## 公開資料との比較

2026-10-07に本文を確認。採用したのは必要時の参照、明確な境界、焦点を絞った検証であり、各repositoryの運用一式ではない。

- [OpenAI AGENTS公式ガイド](https://learn.chatgpt.com/docs/agent-configuration/agents-md): rootから現在directoryへの指示読込。全階層に優先すると宣言するより、適用される指示と依頼を確認する表現にした。
- [OpenAI、2026-09-11の指針](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra): 文書の条件付き参照と承認境界の見直しを採用。モデルに任せるため検証を全削除する判断はせず、このrepositoryのAPI/UI接続を残した。
- [OpenAI Multi-agent](https://developers.openai.com/api/docs/guides/agents-api/multi-agent): 独立タスクと共有編集の調整。全作業を分業する義務にはしない。
- [Anthropic context engineering、2025-09-29](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): 必要時の探索と短い再開情報を採用。固定ファイル一覧だけで関連境界を見落とさない。
- [Next.jsのAGENTS実例](https://github.com/vercel/next.js/blob/8d8c0cd51804d326083dc621f9a9f13124549d5f/AGENTS.md): focused checksと結果再利用を参考にした。全README読込、大規模frameworkのbootstrap、独自PR手続きは持ち込まない。
- [OpenAI Agents PythonのAGENTS実例](https://github.com/openai/openai-agents-python/blob/911f106d9987a61a59654b046b6e891b212b00e3/AGENTS.md): 条件別参照と変更範囲に対応した検証を参考にした。SDK固有の多数のskillや禁止事項は複製しない。

## 内容検証

以下は候補の文面を実作業状況に当てはめた確認であり、AIの実運用試験ではない。

| 状況 | 候補の判断 |
|---|---|
| 既存仕様内で実装案が二つある | 自律的に選び完了まで進む。受入条件変更は確認する。 |
| 古いMDと実装が違う | 事実を確認し古い記述を区別。権限仕様自体が不明ならその部分を確認する。 |
| 別機能のuntrackedがある | 保全して続行。同じ対象への他者変更なら上書きしない。 |
| worktree禁止のChild | 禁止を守りcheckoutで同時branch切替をしない。無断の隔離作成をしない。 |
| Child二つがAPI・型を共有する | 担当・依存を確認し、契約変更を共有して接続を検証する。 |
| 検証後にChildまたは親が進む | 検証済みChild SHAを選び、親差分に必要な検証を更新する。 |
| mergeに古いAGENTSや未統合MDが入る | 親ルールを巻き戻さず、当時のChild記録と親の現在状態を分ける。 |
| UI変更で実接続確認ができない | 未検証と阻害条件を報告。mockのPASSだけで完了にしない。 |
| 文書のみの候補変更 | 差分・参照・整合性を確認。Web全テスト/buildを反復しない。 |
| commit/pushが既に依頼されている | 指定review branchで実行し再承認を求めない。mainへは統合しない。 |

常設AGENTSは4,778 → 3,891 bytes（18.6%削減）、7節 → 4節。上記10状況の内容整合性、UTF-8・末尾改行・相対リンク、差分の空白診断を確認した。公開事例の固定SHAでAGENTSの同一性も確認した。

変更は3文書に限定。アプリコード・依存・テスト設定は変更していないため、アプリのテストやbuildは実行していない。候補の実運用効果は未検証であり、採用後の作業で評価する。
