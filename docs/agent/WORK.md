# AGENTS review WORK

## Goal
AI開発を速くするために規則を増やすのではなく、失敗コストが高い箇所だけをguardrailとして残す。

## Repository findings
- Epic/Child分割は1作業の責任を狭め、実装時のコンテキストを減らす点で有効。
- 一方、Child branchが多いため個別テスト成功だけでは親での統合品質を保証できない。共有境界と代表フローの統合検証が必要。
- Ticket Epicのように現在仕様・実装・検証・次作業を1文書へ圧縮する形は再開コンテキストとして有効。過去MDを常時読む必要はない。
- v2は方向性は良いが、AGENTS改善サイクル自体を恒常ルール化しており、通常作業に不要なmeta-contextが残る。
- 「不確実なら確認」は広すぎると停止を増やす。安全に既存パターンを踏襲できる判断はAIに委ね、仕様・契約・破壊的操作だけを承認境界にする。

## Candidate decisions
- 維持: 1責任、必要時だけ追加探索、dirty state保護、検証事実の厳密化。
- 強化: Childの出力契約と統合担当のshared-boundary検証。
- 縮約: テストは全再実行固定ではなく、近いテストから影響範囲へ段階的に拡大。
- 削除: 通常AGENTSからAGENTS自身の改善サイクル、トレンド調査義務、進行中Ticket固有のrollout情報。
- 明確化: 質問は安全に継続不能な場合だけ。既存パターンで可逆な判断は自律実行。

## External comparison
2026-10-07時点のOpenAI Codex/GitHub Copilot/公開AGENTS事例を比較した。共通して有用なのは、永続的なrepository guidance、局所的な規約、正しいbuild/test手順、必要範囲へのcontext限定である。公開事例の長い規約をそのまま移植せず、このrepositoryで実際に事故コストが高いGit安全性とChild統合を優先した。
