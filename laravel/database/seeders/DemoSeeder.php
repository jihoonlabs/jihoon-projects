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

            foreach ([
                [
                    'name' => '採用チームの業務改善',
                    'tickets' => [
                        ['BACKLOG', '面接評価シートを見直す'],
                        ['TODO', '面接日程の案内を作成する'],
                        ['IN_PROGRESS', '応募者向けFAQを更新する'],
                        ['IN_REVIEW', '面接後のフォロー手順を確認する'],
                        ['DONE', '募集要項の共有先を整理する'],
                    ],
                ],
                [
                    'name' => 'リファラル採用の準備',
                    'tickets' => [
                        ['TODO', '社員向け紹介案内を作成する'],
                        ['IN_PROGRESS', '紹介制度の説明資料を更新する'],
                        ['DONE', '説明会の日程を共有する'],
                    ],
                ],
            ] as ['name' => $name, 'tickets' => $tickets]) {
                $project = Project::create(['name' => $name]);
                $project->forceFill([
                    'created_by' => $user->id,
                    'next_ticket_number' => count($tickets) + 1,
                ])->save();
                $project->members()->attach($user->id, ['role' => 'leader', 'permission' => 'write']);

                foreach ($tickets as $index => [$status, $title]) {
                    Ticket::create([
                        'project_id' => $project->id,
                        'issue_key' => sprintf('%s-%02d', $project->project_key, $index + 1),
                        'title' => $title,
                        'description' => '体験用の架空チケットです。候補者の氏名や連絡先は入力せず、詳細の編集、コメント、状態変更をお試しください。',
                        'status' => $status,
                        'priority' => 'MEDIUM',
                        'position' => 0,
                        'assignee_id' => $user->id,
                    ]);
                }
            }
        });
    }
}
