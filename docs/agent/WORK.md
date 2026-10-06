# AGENTS独立レビュー WORK

## 目的・範囲
docs/agents-v2から独立した比較候補を作成する。変更対象はAGENTS.mdとこのWORK/MANUALのみ。アプリ変更、元ブランチ更新、main統合は対象外。

## 基準
- 原本: docs/agents-v2 @ 66a70de5ba5a68605b26695d2d568cb2d64ea68a
- 候補: docs/agents-v2-review-integration-20261007
- 実作業の比較対象: feature/ticket-v1-integration @ 290f895504b544461fb89b99e54dc880f88ba2d8
- 元ブランチのコードとTicket統合済みコードは異なる。原本へTicketを取り込まない。

## 完了条件
- 元の3文書、TicketのEpic/Child/統合MD、関連コード・テスト設定を確認する。
- 公式ガイド、context engineering、公開AGENTS例を実際に読み、採用/不採用理由をMANUALに残す。
- 必須の安全境界を保ち、通常の実装判断と証拠で解ける文書差異による不要停止を減らす。
- 文書diff/空白・整合性を確認し、候補だけをcommitしてリモートへ反映する。

## 状態
独立候補を作成。検討内容・検証範囲はMANUALを参照。
実運用評価と最終採用は未実施。進行中のTicketへ遡及適用しない。

## 文書検証
- AGENTS本文: 1856 → 1685文字（9%削減、改行込み）。根拠は常時読まないMANUALへ分離。
- 変更は指定3文書のみ。空白検査と承認/停止/統合/未検証の6シナリオを机上確認。
- アプリテスト・実ブラウザー・実運用評価は今回未実行。
