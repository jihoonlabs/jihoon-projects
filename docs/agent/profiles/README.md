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

## 最初の実験Profile
- `continuation`: 既存作業を継続して実装・検証・統合する。
- `zero-base`: 既存結論を前提にせず独立に再検討する。

作業MDで例:
```
agent_profile: continuation
```

または:
```
agent_profile: zero-base
```

実作業で明確な必要が出るまでProfileを増やさない。
