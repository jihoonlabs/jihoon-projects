# AGENTS改善 WORK

## Version
v2.1 independent review candidate

## Goal
v2.1を基準に、追加ルールを増やさず統合handoffと検証効率だけを再確認する。

## Review findings
- v2で広かった停止条件はv2.1で十分に改善された。既存パターンから解ける小判断、無関係なdirty/untrackedで止めない方針は維持する。
- Childのcommit SHAをParentが採用状態として所有する方式は、異なるAI・端末間の引継ぎにも有効なので維持する。
- Child handoffには成功結果だけでなく、統合側が知る必要のある「残る制約」を含める。
- 検証は変更近傍から始め、影響範囲に応じて広げる。常時フルテストは要求しない。
- これ以上の管理層、固定コンテキスト量、特定AI向けルールは追加しない。

## Decision
v2.1の構造をそのまま採用し、AGENTS.mdの実質変更は上記2点だけとする。
AGENTS改善自体は通常作業の常時ルールへ戻さない。

## Validation target
次の新規作業で、Child handoffの制約欠落が減るか、検証時間を増やさず親統合の回帰を捕捉できるかを観察する。
