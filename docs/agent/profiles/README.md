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

## WORKとMANUAL
- WORKはAI同士のhandoff用。責任、依存関係、採用SHA、検証結果、残る制約・未検証事項など、次のAIが作業を継続・統合するために必要な情報を持つ。
- MANUALはユーザー向けの記録。後から読んで、そのBranchでなぜ作業し、何を変え、何を確認し、現在どうなっているかを短時間で把握できるようにする。
- 各Childは自分のWORKとMANUALを持ち、同じParentの共有MANUALを並行編集しない。
- WORKとMANUALは同じ内容を複製しない。AI向けの詳細はWORK、ユーザーが後で読む事実と結果はMANUALへ分ける。
- Parent/Epic統合時は、必要に応じてIntegration Profile/AgentがChild WORKの採用SHA・検証・制約を確認し、Child MANUALを基にParent/Epic MANUALを整理する。
- 最終MANUALには実際に採用された結果だけを残し、Childの作業途中の説明や重複をそのまま積み上げない。
- 小さい作業でも「そのBranchで何をしたか」は残す。ただし文書量は作業規模に合わせ、不要に長くしない。

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
