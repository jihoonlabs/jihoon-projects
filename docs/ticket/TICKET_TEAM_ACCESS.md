# Ticket Project Access

## 目的と範囲
Ticket をProject単位で分離し、小規模チームがProjectメンバー、権限、担当者、コメントを安全に扱えるようにする。このChildではLaravelのProject/Member APIとTicket権限境界、およびReactのProject選択・メンバー管理・権限別ボード操作を実装する。

## 確定した権限・UX
- アプリ権限は `user` / `admin`、Project内の役割は `leader` / `member`、Ticket権限は `read` / `write` として分離する。
- adminは全Projectを扱える。Project leaderは所属Projectのメンバーを追加・変更・削除できる。
- readはProject内Ticketの閲覧とコメント投稿、writeはそれに加えてTicket作成・編集・削除・担当者変更・状態変更ができる。
- コメントは投稿者のみ編集でき、投稿者またはadminが削除できる。
- Board上部のProject選択で表示Ticketを切り替える。leader/adminにはメンバー管理ダイアログを表示し、readメンバーはTicket詳細とコメントを利用できるが、Ticket変更操作は表示しない。
- Ticketの担当者は選択Projectのメンバーに限り、未割り当ても許可する。
- 既存Ticketは `General` Projectへ移行する。移行時点でactiveだった利用者のみ `General` の `member/write` とし、新規利用者は自動参加させない。

## 実装状態
- `users.role`、`projects`、`project_members` と必須 `tickets.project_id`、既存Ticketの `General` へのバックフィル、User/Project/TicketのEloquent関係を実装。
- Project CRUDはadmin限定。メンバー一覧はProjectメンバーに公開し、leader/adminがメンバーの追加・役割/権限変更・削除を行える。
- TicketとコメントAPIにProject membership/read/write境界を適用し、担当者を同一Projectメンバーに限定。
- React API境界でLaravelのsnake_case `project_id` を `projectId` に変換。Ticket作成時に選択Project IDを送信。
- Boardは許可されたProjectとそのTicketを切り替え、Projectメンバーを担当者候補に表示。leader/admin用メンバー管理ダイアログ、read/write別Ticket操作、adminのコメント削除を実装。
- `/api/auth/me` とログイン/登録レスポンスに `role` を含め、admin UI権限判定に利用。

## 検証
- Laravel全テスト: 97件、431 assertions 通過。Pint通過。
- React全テスト: 124件通過。TypeScript (`tsc --noEmit`)、ESLint、production build通過。
- Chrome Headlessの実ブラウザーで認証、Project一覧/切替、leaderによるメンバー追加・役割/権限変更、選択Projectのメンバーを担当者にしたTicket作成、Ticket編集/状態変更/削除、コメント作成/編集/削除を確認。
- readメンバーでもブラウザーで許可ProjectとTicket詳細を参照でき、Ticket変更・メンバー管理操作が表示されず、コメント投稿が可能なことを確認。
- ブラウザー確認は専用の一時SQLite DBとローカルサーバーで実施。共有環境・本番DBへのmigrationや本番デプロイは未検証。

## 次の作業
- 対象リポジトリは `jihoonlabs/jihoon-projects`。Epicは `feature/ticket`、Childは `feature/ticket-team-access`。
- Project Access実装は `129145e535a0051883d45f52742069995508f73b` としてChildへpush済み。直前のEpic基準commitは `80b830dbc8ce90ae6c84c2e4fd5cb3ed3536e300` で、Childはその子孫。
- Childの実装・自動検証・ブラウザー確認は完了。Epic統合は未実施。統合時はEpicの最新状態を取得し、cleanなworktreeでfast-forward可能性を確認してから `--ff-only` と全体検証を行う。
- 次のChild候補はTicket `position` のDB/API永続化。現在はクライアント内だけで順序を保持する。Activity/HistoryはV1後の改善候補とする。
- 共有環境・本番DB migration、本番デプロイ、Epic統合後の検証は未実施。
