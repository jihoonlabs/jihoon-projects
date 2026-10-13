# Project Color Child — WORK

## 目的と範囲
- Branch: `feature/ticket-project-colors`。基準Epic SHA: `15dea4305d526c2d4bdba5b6d2476de0724528c0`。
- 不変の`project_key`からTicketカードの控えめな枠線色を決定する。Project名変更や再接続後も色を維持する。
- React表示と関連テストのみ。DB、Laravel API、Ticket key/番号、状態・優先度の見せ方、選択・DnDの動作は変更しない。

## 実装
- Project APIの`project_key`を画面用`Project.projectKey`へ変換して保持する。
- 大文字化した固定keyにFNV-1a hashを適用し、HSL hueを決める。彩度42%、明度80%の色をCSS変数としてカードへ渡す。
- 選択中Projectのkeyを通常カードとDragOverlayへ渡し、通常/hover時のborderだけに使用する。keyがないlegacy Projectは既定borderを使う。
- Project名とTicketのissue key・状態・優先度は引き続き文字で表示され、色だけを識別手段にしない。

## 検証
- 関連Vitest: 3 files / 9 tests passed。React全体: `pnpm test:run` — 23 files / 132 tests passed。
- `pnpm exec tsc --noEmit`、`pnpm lint` passed。
- Production build: `next build --webpack` passed。既存`.next`を使わない一時コピーで実行した。
- Chrome 154実ブラウザー: Sanctumログイン後にProject `FLF`と`KTT`を作成し、同Project内2枚の枠線が一致し、別Projectの枠線が異なることを確認。Project名変更後の再読込でもkeyと色が維持された。
- ブラウザーでKEY番号、status、priority、sortable roleとkeyboard tab focusを確認。実ポインターによるDnD操作はこのChildでは未実施。既存DnDの回帰テストは全React suiteでpassed。
- ブラウザー用DBは一時SQLite。既存DBと`.env`は使用・変更していない。

## 現在状態
- 実装・自動検証・実ブラウザー確認済み。Childは未commit・未push・Epic未統合。
- 次は最終diffを確認して結果を報告する。commit/push/Epic・main統合は別途承認が必要。
