# Ticket Member Recovery Child

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-member-recovery
role: child
status: validated-user-review-pending
parent_branch: feature/ticket
base_sha: 6f744b2b2c924938b2f6c69f3c87f361997c5993

## Responsibility / Boundary
既存のProject member取得失敗からボード上で再試行できるようにし、Project切替とメンバー管理後の遅延取得が権限・担当者候補を上書きしないようにする。API・DB・権限仕様は変更しない。

## Validation / Handoff
- member取得のerrorをProject一覧errorから分離し、同じProjectで再試行できる。取得成功で無関係なProject一覧errorを消さない。
- dialogを閉じた後の再取得もeffectの遅延応答guardへ統一した。再確認中は古いmembershipを操作判断に使用せず、別Projectへの遅延応答を無視する。
- dialogによるmember変更のrevisionを記録し、変更前のboard取得が最新memberを上書きしない。
- 修正前コードで新規4 testsの失敗を確認。対象View 32 tests、React全29 files / 204 tests、TypeScript、ESLint、変更TSX/CSSのPrettier、最終コードのproduction buildが成功。
- 今回は実browser/実Laravel接続を再実行していない。React/API境界の遅延promiseで検証した。利用者の実画面確認と指摘修正は残る。
