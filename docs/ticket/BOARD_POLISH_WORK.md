# Ticket Board Design Child

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-board-design
role: child
status: validated-user-review-pending
parent_branch: feature/ticket
base_sha: a02f37781e0c2fbc5d8852e1f26fcaecb2edf582

## Responsibility / Boundary
利用者の実画面指摘に合わせ、Header/toolbarの階層と余白、Project色の強さ、カードの可読性、dark-system下の入力を調整する。既存機能・権限・API・DBは変更しない。

## Validation / Handoff
- アプリ検証SHA: `c5417c648f1380dd673b26f1c8317c26ad817346`。公開treeと検証済みローカルファイルの一致を確認した。
- 共通Headerを小さくし、board toolbarをProject/操作とcontext/filterの2段に整理。管理ボタンの表示を短くし、既存accessible nameと操作を維持した。
- Project keyから決まる色を維持し、card背景をwhiteと混色して淡くした。タイトルのweight/line-heightと列の幅・間隔を調整した。
- boardとheaderをlight color-schemeとし、dark-systemでも検索入力の背景/文字を明示した。
- React全29 files / 208 tests、TypeScript、ESLint、変更TSX/CSSのPrettier、production buildが成功。
- 実Chromiumのdark-systemで1440/940/393pxを確認。ページ横overflowなし、検索背景/文字、8 cards、mobile detailの画面内収まり、pageerror 0件を確認。1440pxは全5列を表示し、940/393pxはboard内で横scrollする。画像も目視確認した。API fixtureによる表示検証であり、実Laravel接続ではない。
- 利用者による修正後画面の確認は残る。API・DB・権限変更はない。
