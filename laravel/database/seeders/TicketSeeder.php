<?php

namespace Database\Seeders;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Database\Seeder;

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
                'issue_key' => sprintf('%s-%02d', $project->project_key, 1),
                'title' => 'ログインAPIおよびJWTトークン処理の連携',
                'description' => 'Laravelバックエンド認証APIの構築',
                'status' => 'DONE',
                'priority' => 'HIGHEST',
                'assignee_id' => $user->id,
            ],
            [
                'issue_key' => sprintf('%s-%02d', $project->project_key, 2),
                'title' => 'JiraスタイルかんばんボードのUI実装',
                'description' => 'Next.jsベースのドラッグ＆ドロップボード構築',
                'status' => 'IN_PROGRESS',
                'priority' => 'HIGH',
                'assignee_id' => $user->id,
            ],
            [
                'issue_key' => sprintf('%s-%02d', $project->project_key, 3),
                'title' => 'チケット検索および担当者フィルターの実装',
                'description' => 'リアルタイム検索クエリの状態バインディング',
                'status' => 'IN_REVIEW',
                'priority' => 'MEDIUM',
                'assignee_id' => $user->id,
            ],
            [
                'issue_key' => sprintf('%s-%02d', $project->project_key, 4),
                'title' => 'DND-Kit マウストラッキングオーバーレイのバグ修正',
                'description' => 'CSS Translateによるポータルアニメーション調整',
                'status' => 'TODO',
                'priority' => 'LOW',
                'assignee_id' => null,
            ],
            [
                'issue_key' => sprintf('%s-%02d', $project->project_key, 5),
                'title' => 'Laravel DBマイグレーションおよびAPI接続',
                'description' => 'REST APIエンドポイントおよびCORSの設定',
                'status' => 'BACKLOG',
                'priority' => 'LOWEST',
                'assignee_id' => null,
            ],
        ];

        foreach ($tickets as $ticketData) {
            Ticket::updateOrCreate(
                ['project_id' => $project->id, 'title' => $ticketData['title']],
                [...$ticketData, 'project_id' => $project->id]
            );
        }

        $project->forceFill(['next_ticket_number' => count($tickets) + 1])->save();
    }
}
