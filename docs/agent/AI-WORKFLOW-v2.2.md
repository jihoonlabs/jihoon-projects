# AIを活用した開発プロセス — 公開実績 v2.2

## このページの位置づけ

公開版 [AGENTS v2.1](AGENTS-v2.1.md) は、このリポジトリの実作業で使用したルールです。v2.1の公開後に適用した作業を、公開コミットとPRに結びつけて示します。

ここでいうv2.2は、ポートフォリオの説明と根拠を更新した版です。AGENTSのルール本文をv2.2へ変更したものではありません。内部のプロンプト、運用設定、非公開の作業記録は掲載しません。

## ルールが更新された経緯

| 時期 | 変更 | 公開根拠 |
| --- | --- | --- |
| 2026-09-28 | AI作業ルールをリポジトリに導入 | [e4af694](https://github.com/jihoonlabs/jihoon-projects/commit/e4af694426e1b693952d37ec1d048fb7a3a69f85) |
| 2026-10-07 | 実作業と独立レビューで確認された改善を反映し、v2.1として公開 | [fcf99a3](https://github.com/jihoonlabs/jihoon-projects/commit/fcf99a39a7d518abbe690eb2723563323a883eeb) |

v2.1では、安全に判断できる小さな事項の自律化、ChildからParentへの引き継ぎ、影響に応じた検証、無関係なGit変更の保護、根拠のある規則改善を反映しました。変更の詳細は [MANUAL v2.1](MANUAL-v2.1.md) にまとめています。

## 実際の適用を確認できる公開作業

### Ticketテストの統合 — 2026-10-25〜26

MSWを使い、ボードの作成・更新・コメント・プロジェクト操作の流れを統合して検証しました。各作業はPRで確認され、mainに取り込まれています。

- [PR #42](https://github.com/jihoonlabs/jihoon-projects/pull/42): ボードAPI統合テスト
- [PR #46](https://github.com/jihoonlabs/jihoon-projects/pull/46): Ticketテスト品質改善の統合
- [PR #49](https://github.com/jihoonlabs/jihoon-projects/pull/49): ボードの利用者フロー統合検証

PR #49の記録には、React 54ファイル・242テストと、関連する型・Lint・整形検査の結果が記載されています。

### Attendance APIと画面の統合 — 2026-10-27

APIとReact画面を別々のPRで実装した後、統合PRで出退勤と履歴の流れをまとめました。

- [PR #67](https://github.com/jihoonlabs/jihoon-projects/pull/67): Laravel Attendance API
- [PR #68](https://github.com/jihoonlabs/jihoon-projects/pull/68): 出退勤画面とナビゲーション
- [PR #69](https://github.com/jihoonlabs/jihoon-projects/pull/69): API・画面の統合と検証記録

PR #69には、統合対象に対するLaravelテストとPint、Reactテスト・Lint・TypeScript・Prettier・production buildの実行結果が記録されています。

## 読む順序

1. 実作業で使用したルール: [AGENTS v2.1](AGENTS-v2.1.md)
2. ルール改訂作業の目的と判断: [WORK v2.1](WORK-v2.1.md)
3. v2.1で変更した内容: [MANUAL v2.1](MANUAL-v2.1.md)
4. 後続の適用例と公開根拠: このページ
