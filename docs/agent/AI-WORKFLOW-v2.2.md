# AIを活用した開発プロセス — 公開実績 v2.2

## このページの位置づけ

公開版 [AGENTS v2.1](AGENTS-v2.1.md) は、このリポジトリの実作業で使用したルールです。v2.1の公開後に適用した作業を、公開commit・PRと結びつけて示します。

ここでいうv2.2はポートフォリオの説明・証拠の更新番号です。AGENTSのルール本文をv2.2へ変更したものではありません。内部のprompt、運用設定、非公開作業記録は掲載しません。

## ルールが更新された経緯

| 時期 | 変更 | 公開根拠 |
| --- | --- | --- |
| 2026-09-28 | AI作業ルールをリポジトリに導入 | [e4af694](https://github.com/jihoonlabs/jihoon-projects/commit/e4af694426e1b693952d37ec1d048fb7a3a69f85) |
| 2026-10-07 | 実作業と独立レビューで確認された改善を反映し、v2.1として公開 | [fcf99a3](https://github.com/jihoonlabs/jihoon-projects/commit/fcf99a39a7d518abbe690eb2723563323a883eeb) |

v2.1では、安全に判断できる小さな事項の自律化、ChildからParentへの引き継ぎ、影響に応じた検証、無関係なGit変更の保護、根拠のある規則改善だけを扱う内容を反映した。詳しい変更は [MANUAL v2.1](MANUAL-v2.1.md) にまとめている。

## 실제 적용을 확인할 수 있는 공개 작업

### Ticketテストの統合 — 2026-10-25〜26

MSW를 사용해 보드의 생성·수정·댓글·프로젝트 흐름을 통합 검증했다. 작업은 후속 검토를 거쳐 main에 반영됐다.

- [PR #42](https://github.com/jihoonlabs/jihoon-projects/pull/42): ボードAPI統合テスト
- [PR #46](https://github.com/jihoonlabs/jihoon-projects/pull/46): Ticketテスト品質改善の統合
- [PR #49](https://github.com/jihoonlabs/jihoon-projects/pull/49): 보드 사용자 흐름 통합 검증

PR 기록에는 변경별 테스트와 타입·Lint 등 실행 결과가 남아 있다. PR #49 기록은 React 54개 파일·242개 테스트와 관련 정적 검사가 통과했다고 밝힌다.

### Attendance API와 화면 통합 — 2026-10-27

API와 React 화면을 별도 PR로 구현한 뒤 통합 PR에서 출퇴근·이력 흐름을 함께 반영했다.

- [PR #67](https://github.com/jihoonlabs/jihoon-projects/pull/67): Laravel Attendance API
- [PR #68](https://github.com/jihoonlabs/jihoon-projects/pull/68): 출퇴근 화면과 내비게이션
- [PR #69](https://github.com/jihoonlabs/jihoon-projects/pull/69): API·화면 통합 및 최종 검증 기록

PR #69에는 통합 대상의 Laravel 테스트와 Pint, React 테스트·Lint·TypeScript·Prettier·production build 결과가 기록돼 있다.

## 읽는 순서

1. 실제 작업 규칙: [AGENTS v2.1](AGENTS-v2.1.md)
2. 규칙 개정 작업의 범위와 판단: [WORK v2.1](WORK-v2.1.md)
3. v2.1에서 바뀐 내용: [MANUAL v2.1](MANUAL-v2.1.md)
4. 후속 적용 사례와 공개 근거: 현재 페이지

