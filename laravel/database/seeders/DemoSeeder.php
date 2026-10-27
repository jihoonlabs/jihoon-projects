<?php

namespace Database\Seeders;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use RuntimeException;

class DemoSeeder extends Seeder
{
    public function run(): void
    {
        if (! config('demo.enabled')) {
            throw new RuntimeException('TICKET_DEMO_MODE=true is required.');
        }

        // 既存アプリや勤怠データのあるDBに公開アカウントを追加しない。
        $businessTables = [
            'users',
            'projects',
            'project_members',
            'project_audit_events',
            'tickets',
            'ticket_comments',
            'attendance_records',
        ];

        foreach ($businessTables as $table) {
            if (DB::table($table)->exists()) {
                throw new RuntimeException('DemoSeeder requires an empty dedicated demo database.');
            }
        }

        DB::transaction(function () {
            $user = User::create([
                'name' => 'デモ利用者',
                'email' => 'demo@example.com',
                'password' => 'TicketDemo2026!',
            ]);
            $user->forceFill(['email_verified_at' => now()])->save();

            $project = Project::create(['name' => '製品サイトの改善']);
            $project->forceFill(['created_by' => $user->id, 'next_ticket_number' => 6])->save();
            $project->members()->attach($user->id, ['role' => 'leader', 'permission' => 'write']);

            foreach ([
                ['BACKLOG', '利用者の要望を整理する'],
                ['TODO', '検索フォームの改善'],
                ['IN_PROGRESS', 'モバイル表示を調整する'],
                ['IN_REVIEW', '入力エラーの表示を確認する'],
                ['DONE', 'ヘルプ文言を更新する'],
            ] as $index => [$status, $title]) {
                Ticket::create([
                    'project_id' => $project->id,
                    'issue_key' => sprintf('%s-%02d', $project->project_key, $index + 1),
                    'title' => $title,
                    'description' => '体験用の架空チケットです。詳細の編集、コメント、ボードでの移動をお試しください。',
                    'status' => $status,
                    'priority' => 'MEDIUM',
                    'position' => 0,
                    'assignee_id' => $user->id,
                ]);
            }
        });
    }
}
