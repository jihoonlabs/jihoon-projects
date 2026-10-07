# AGENTS v2.1 再review

作成日: 2026-10-07。基準とreview branchは [WORK](WORK.md) を参照。
この文書は比較根拠と検証結果であり、通常作業での必読にはしない。

## 判断

v2.1は候補として十分使える。広すぎた停止条件と無関係なdirtyでの全面停止を改善し、Child SHAを親で管理し、分解と統合の向きも明示している。特定のAI・IDEに依存しない。
最終採用前には次の曖昧さを直す価値がある。

| v2.1の記述 | 今回の判断 |
|---|---|
| 既存パターンから「一意」に決まる小判断のみ自律、他方で新UX等は確認 | 承認済み機能内の複数の実装案まで待ち得る。依頼範囲内の実装判断は進め、結果を変える未承認仕様だけ確認する。 |
| Childは検証結果を残し、親は採用Child SHAと統合状態を管理 | 未検証の境界・制約も引継ぐ。親は統合後HEADとその検証状態を持ち、Child単体の検証と取り違えない。 |
| 競合は報告し勝手に解消しない | Ticketの統合記録にはAGENTS競合の解消がある。承認済み統合の既存契約内の競合は解消し、仕様選択を要する場合だけ確認する。 |
| 各branchで関連テストと必要な静的検証 | 変更に最も近いテストから始め、影響する接続・契約へ広げる。全タスクへ同じ段階や全suiteを強制しない。 |
| 作業MDとMANUALに分ける | 再開・引継ぎ・利用説明が必要な時に作成/更新する。小修正の定型文書や親MDへのChild履歴複製は不要。 |
| AGENTSが全AI作業に優先 | リポジトリ内で適用される指示として扱い、承認・安全境界は作業MDで変えない。絶対的な優先宣言は不要。 |

根拠: [v2.1のAGENTS](https://github.com/jihoonlabs/jihoon-projects/blob/be26cb1300ba274370513226c4ac53cf4bd1e610/AGENTS.md)、[v2.1のWORK](https://github.com/jihoonlabs/jihoon-projects/blob/be26cb1300ba274370513226c4ac53cf4bd1e610/docs/agent/WORK.md)、[v2.1のMANUAL](https://github.com/jihoonlabs/jihoon-projects/blob/be26cb1300ba274370513226c4ac53cf4bd1e610/docs/agent/MANUAL.md)。実例として[Ticket統合記録](https://github.com/jihoonlabs/jihoon-projects/blob/feature/ticket-order-persistence-integration/docs/ticket/ticket-order-persistence-integration.md)のAGENTS競合解消を確認した。

## 削除・縮小

常設の「最小必須」を宣言する説明と長い作業MD/MANUAL定義を縮めた。親MDはRouterに限定し、MANUALは必要時のみ更新する。新しい承認手続き、特定ツール、固定の全文読込・テスト回数は追加しない。

## 文書検証

差分は指定3文書のみ。承認済み機能内の複数案、未承認の権限変更、Child未検証、親のHEAD前進、契約内のmerge競合、関係ないdirty、UI/API接続、文書だけの変更を文面に当てはめた。
UTF-8、改行、相対参照、空白を確認。アプリコード・設定を変更していないためアプリテストは実行していない。実運用の質問回数、誤統合率、検証漏れの改善効果は未測定。
