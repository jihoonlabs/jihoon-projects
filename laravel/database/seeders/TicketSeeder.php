<?php

namespace Database\Seeders;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class TicketSeeder extends Seeder
{
    public function run(): void
    {
        // テスト用担当者生成
        $user = User::firstOrCreate(
            ['email' => 'jihoon@example.com'],
            ['name' => 'パク・ジフン', 'password' => bcrypt('password')]
        );
        $project = Project::firstOrCreate(['name' => 'General']);
        $members = User::where('status', 'active')
            ->pluck('id')
            ->mapWithKeys(fn ($id) => [
                $id => ['role' => 'member', 'permission' => 'write'],
            ])
            ->all();
        $project->members()->syncWithoutDetaching($members);

        $tickets = [
            [
                'title' => 'ログインAPIおよびJWTトークン処理の連携',
                'description' => 'Laravelバックエンド認証APIの構築',
                'status' => 'DONE',
                'priority' => 'HIGHEST',
                'assignee_id' => $user->id,
            ],
            [
                'title' => 'JiraスタイルかんばんボードのUI実装',
                'description' => 'Next.jsベースのドラッグ＆ドロップボード構築',
                'status' => 'IN_PROGRESS',
                'priority' => 'HIGH',
                'assignee_id' => $user->id,
            ],
            [
                'title' => 'チケット検索および担当者フィルターの実装',
                'description' => 'リアルタイム検索クエリの状態バインディング',
                'status' => 'IN_REVIEW',
                'priority' => 'MEDIUM',
                'assignee_id' => $user->id,
            ],
            [
                'title' => 'DND-Kit マウストラッキングオーバーレイのバグ修正',
                'description' => 'CSS Translateによるポータルアニメーション調整',
                'status' => 'TODO',
                'priority' => 'LOW',
                'assignee_id' => null,
            ],
            [
                'title' => 'Laravel DBマイグレーションおよびAPI接続',
                'description' => 'REST APIエンドポイントおよびCORSの設定',
                'status' => 'BACKLOG',
                'priority' => 'LOWEST',
                'assignee_id' => null,
            ],
        ];

        DB::transaction(function () use ($project, $tickets) {
            $lockedProject = Project::query()->lockForUpdate()->findOrFail($project->id);
            $nextNumber = (int) $lockedProject->next_ticket_number;
            $keyPattern = '/^'.preg_quote($lockedProject->project_key, '/').'-(\d+)$/';

            // Keep the counter ahead of existing keys if a prior seed left it stale.
            foreach ($lockedProject->tickets()->pluck('issue_key') as $issueKey) {
                if (preg_match($keyPattern, (string) $issueKey, $matches) === 1) {
                    $nextNumber = max($nextNumber, (int) $matches[1] + 1);
                }
            }

            foreach ($tickets as $ticketData) {
                $ticket = Ticket::query()->firstOrNew([
                    'project_id' => $lockedProject->id,
                    'title' => $ticketData['title'],
                ]);

                if (! $ticket->exists) {
                    $ticketData['issue_key'] = sprintf('%s-%02d', $lockedProject->project_key, $nextNumber++);
                }

                $ticket->fill([...$ticketData, 'project_id' => $lockedProject->id])->save();
            }

            $lockedProject->forceFill(['next_ticket_number' => $nextNumber])->save();
        });

    }
}
