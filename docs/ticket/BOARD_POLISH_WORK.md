# Ticket Comment Reliability Child

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-comment-reliability
role: child
status: validated-user-review-pending
parent_branch: feature/ticket
base_sha: dd5d547430511234336a1c5278244adc14dd39e8

## Responsibility / Boundary
既存コメントの取得・投稿・編集で遅延応答による表示や入力の消失を防ぐ。取得中/失敗/空一覧を区別し、取得失敗から再試行できるようにする。API・DB・権限仕様は変更しない。

## Validation / Handoff
- アプリ検証SHA: `768a438461051b77d117059315771947295bc060`。公開treeと検証済みローカルファイルの一致を確認した。
- 取得中は投稿を抑止し、遅い一覧応答が投稿結果を消す競合を防ぐ。取得失敗は空一覧と区別し、下書きを保持したまま再試行する。
- 投稿成功で消すのは送信時点と同じ下書きだけ。編集中の保存待ちは入力を無効化し、失敗時に入力を維持する。ref guardで重複送信を抑止する。
- Ticket IDごとにコメントstateを分離し、切替前の下書き・遅延GET/POST応答が次のTicketへ混入しない。
- 対象13 tests、React全29 files / 200 tests、TypeScript、ESLint、変更TSXのPrettier、production buildが成功。遅延GET、取得失敗/再試行、POST中の次の下書き、重複送信、Ticket切替後の遅延GET/POST、編集失敗を確認した。
- 今回は実browser/実Laravel接続を再実行していない。前回の一時runtimeは現環境に残っておらず、今回の結果はReactの遅延promiseによる検証。Backend変更はない。利用者の実画面確認と指摘修正は残る。
