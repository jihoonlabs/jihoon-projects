# Ticket Project Operations Child

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-project-operations
role: child
status: validated-browser-pending
parent_branch: feature/ticket
base_sha: 07db066adb8b9171531680c5b297d25c88cbd02f

## Responsibility
既存APIのProject rename/archive/restoreとleader譲渡を画面に接続する。終了ProjectのTicket・コメント・メンバー変更を抑止し、既存の権限契約に画面を合わせる。

## Boundary
Backend API・DB schema・権限を変更しない。renameはadmin、archive/restoreとleader譲渡はadminまたは現在leader。全Ticket完了前のarchive拒否、leader直接変更・追加・削除の禁止を維持する。過去の採用状態はTICKET.mdを参照する。

## Validation / Handoff
- 対象58 tests、React全体29 files / 194 tests、TypeScript、ESLint、変更ファイルのPrettier、production buildは成功。
- 名前変更のadmin制限、archive確認/409拒否/再試行、restore/二重要求防止、終了一覧、adminを含む終了ProjectのTicket・コメント変更抑止を確認した。
- leaderの直接role変更/新leader追加/leader削除のUIを廃止し、専用譲渡を接続した。譲渡成功直後に親のmembershipを更新し、旧leaderの管理権限を残さない。保存後GET失敗は再取得を促し、操作を凍結する。
- archive後に古いProject GETが到着してもactive一覧へ復活させないことを確認した。dialogの保存中dismiss抑止、focus復帰/Tab循環/Escapeにも対応する。
- `next start --hostname 127.0.0.1 --port 3002`で起動成功。hostname指定で既知のnetworkInterfaces制限を回避した。`/login`と`/tickets`のproduction HTTP 200・HTML/Next assetsを確認した。これはbrowserや実backend検証ではない。
- 未検証: 実browserの表示/pointer DnD、frontend→Laravel→DB、MySQL migration・複数接続/row lock。Backend変更はない。モック検証を実接続結果とは扱わない。
- 検証コードSHAは後続handoffに記録する。社内基本機能・利用者指摘・実画面確認が満たされるまでV1全体の完了とは扱わない。
