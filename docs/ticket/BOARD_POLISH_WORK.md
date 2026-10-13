# Ticket List Recovery Child

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-list-recovery
role: child
status: validated-user-review-pending
parent_branch: feature/ticket
base_sha: 1e5f5e8660af43a9cd6518f25674217434fbfba6

## Responsibility / Boundary
Ticket削除成功と後続Project取得失敗を区別し、Ticket一覧取得失敗から画面上で再試行できるようにする。API・DB・権限仕様は変更しない。

## Validation / Handoff
- アプリ検証SHA: `739c51d0f01a9bc601f178280d82715308d8aeb8`。公開treeと検証済みローカルファイルの一致を確認した。
- Ticket削除後のProject取得失敗はboardに表示し、削除済みdetailは閉じる。削除APIそのものの失敗時は既存どおりdetailとTicketを維持する。
- Ticket取得errorに再取得ボタンを接続した。取得中をstatus表示し、再取得失敗時も既存一覧を維持する。Project取得errorとは別に表示する。
- 対象View 36 tests、React全29 files / 208 tests、TypeScript、ESLint、変更TSXのPrettier、production buildが成功。削除成功後のmetadata失敗、初回取得失敗/再試行、再試行の失敗/既存一覧保持、遅延取得中の案内を検証した。
- 今回の実browser/実Laravel接続は未実行。API・DB・権限変更はない。利用者の実画面確認と指摘修正は残る。
