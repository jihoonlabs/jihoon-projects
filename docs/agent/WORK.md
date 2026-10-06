# AGENTS改善 WORK

## Goal
実作業で繰り返す摩擦や高影響リスクだけを根拠に、AGENTSを最小かつ有効に保つ。

## Current review
基準: `docs/agents-v2`

今回確認した主な問題:
- 自律作業と停止条件の境界が重なり、小さな判断でも確認に寄りやすい。
- Child統合の考え方はあるが、共有境界を変更した時にproducer/consumerを一組として検証する条件が弱い。
- 「責任範囲外は変更しない」が強すぎると、直接壊れた利用側の整合修正まで止まりやすい。
- AGENTS、WORK、MANUALに同じ運用方針が重複し、将来driftしやすい。
- AGENTS改善サイクル自体の説明が長く、通常作業へ常時ロードする価値が低い。

## Candidate direction
- AGENTSは恒久guardrail/navigationだけに圧縮する。
- 確認は仕様決定・範囲拡大・破壊的操作・ユーザー意図依存の選択に限定する。
- Childは共有境界を明示し、境界変更時は利用側まで統合検証する。
- 直接壊れたconsumer/test/docの整合修正は作業範囲に含める。
- 検証は狭いfeedback loopから始め、完了時に変更範囲へ拡張する。
- stateはWORK、結果はMANUALに置き、同じ規則を再掲しない。

## Status
2026-10-07: 独立review候補を作成・検証。
