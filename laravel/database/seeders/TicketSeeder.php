<?php

namespace Database\Seeders;

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

        $tickets = [
            [
                'issue_key' => 'TICK-101',
                'title' => 'ログインAPIおよびJWTトークン処理の連携',
                'description' => 'Laravelバックエンド認証APIの構築',
                'status' => 'DONE',
                'priority' => 'HIGHEST',
                'assignee_id' => $user->id,
            ],
            [
                'issue_key' => 'TICK-102',
                'title' => 'JiraスタイルかんばんボードのUI実装',
                'description' => 'Next.jsベースのドラッグ＆ドロップボード構築',
                'status' => 'IN_PROGRESS',
                'priority' => 'HIGH',
                'assignee_id' => $user->id,
            ],
            [
                'issue_key' => 'TICK-103',
                'title' => 'チケット検索および担当者フィルターの実装',
                'description' => 'リアルタイム検索クエリの状態バインディング',
                'status' => 'IN_REVIEW',
                'priority' => 'MEDIUM',
                'assignee_id' => $user->id,
            ],
            [
                'issue_key' => 'TICK-104',
                'title' => 'DND-Kit マウストラッキングオーバーレイのバグ修正',
                'description' => 'CSS Translateによるポータルアニメーション調整',
                'status' => 'TODO',
                'priority' => 'LOW',
                'assignee_id' => null,
            ],
            [
                'issue_key' => 'TICK-105',
                'title' => 'Laravel DBマイグレーションおよびAPI接続',
                'description' => 'REST APIエンドポイントおよびCORSの設定',
                'status' => 'BACKLOG',
                'priority' => 'LOWEST',
                'assignee_id' => null,
            ],
        ];

        foreach ($tickets as $ticketData) {
            Ticket::updateOrCreate(
                ['issue_key' => $ticketData['issue_key']],
                $ticketData
            );
        }
    }
}