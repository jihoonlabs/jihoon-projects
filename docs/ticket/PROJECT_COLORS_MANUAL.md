# ProjectごとのTicket色 — MANUAL

Ticketカードの枠線にProject固有の淡い色を付け、ボード上で視覚的なまとまりを補助します。色は変更されないProject keyから決め、Project名変更やページ再読込後も維持されます。

## 確認結果
- 同じProjectのカードは同じ枠線色になり、別Projectには別の色が表示されました。
- Ticket key、状態、優先度、カードのkeyboard focusとDnD用要素は維持されています。色に加えてProject名とTicket keyも画面に表示されます。
- React 132 tests、TypeScript、ESLint、production buildとChromeブラウザー確認が成功しました。
- テストは一時SQLite DBを使用し、既存DBは変更していません。Child SHA `279556ae55fed766d0299c4bdfb16e4c051b0d3e` はTicket Epicへ統合済みです。Epic統合後にPointer DnDとDB保存も確認済みです。`main`には未統合です。
