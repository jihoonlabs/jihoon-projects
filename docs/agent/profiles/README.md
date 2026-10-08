# Agent Profiles

Agentは万能化せず、作業に必要なProfileだけ切り替えて使う。

## 方向指針
- 共通CoreはGit安全性・検証の正直さ・既存変更の保護など、本当に全作業で必要な最小ルールだけにする。
- 実際の進め方はProfileをレシピとして分離し、作業に合うものだけ選ぶ。
- Profileのversionは優劣ではなく処理範囲を表す。v1で十分な作業にv2を使わない。
- 新versionは既存versionを上書きせず、別の選択肢として追加する。
- Profileは小さく保ち、役割が重なれば統合し、効果がなければ削除する。
- 1つの万能Agentへ統合すること自体を目的にしない。必要なら複数Profileを切り替える。
- 実作業の結果を優先し、合わない設計は固定せず柔軟に見直す。
- 分割しすぎない。役割や判断方法が実際に異なる時だけProfileや作業単位を分ける。

## MANUALとhandoff
- MANUALも固定で一律に分割しない。作業規模・衝突リスク・handoff価値に応じて選ぶ。
- 小さいChildは作業MDに結果・検証・制約を残すだけでもよい。
- 独立したhandoff価値が高いChildや、同一MANUALを複数Childが触って競合しやすい場合はChildごとにMANUALを分ける。
- 複数Childの結果をまとめる必要がある時だけ、Integration Profile/Agentが採用SHA・検証状態・制約を確認してParent/Epic MANUALへ統合する。
- 最終MANUALは採用された結果だけを残し、Child間の重複や作業途中の説明をそのまま積み上げない。
- 文書分割やIntegration Agent自体が管理コストになる場合は使わない。状況に合わなければ統合・削除・簡略化する。

## 最初の実験Profile
- `continuation`: 既存作業を継続して実装・検証・統合する。
- `zero-base`: 既存結論を前提にせず独立に再検討する。
- `integration`: 必要性が確認された場合だけ追加する候補。Childの採用結果をParentへ統合する。

作業MDで例:
```
agent_profile: continuation
```

または:
```
agent_profile: zero-base
```

実作業で明確な必要が出るまでProfileを増やさない。
