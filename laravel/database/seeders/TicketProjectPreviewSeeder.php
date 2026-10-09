<?php

namespace Database\Seeders;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class TicketProjectPreviewSeeder extends Seeder
{
    public function run(): void
    {
        DB::transaction(function () {
            // Preview-only sample. Never modify General or existing tickets.
            $project = Project::query()->firstOrCreate(['name' => 'Demo Project']);
            $tester = User::query()->where('email', 'test@example.com')->first();
            if ($tester !== null) {
                $project->members()->syncWithoutDetaching([
                    $tester->id => ['role' => 'member', 'permission' => 'write'],
                ]);
            }

            $project = Project::query()->lockForUpdate()->findOrFail($project->id);
            $next = (int) $project->next_ticket_number;
            foreach ($project->tickets()->pluck('issue_key') as $key) {
                if (preg_match('/^'.preg_quote($project->project_key, '/').'-(\\d+)$/', (string) $key, $matches)) {
                    $next = max($next, (int) $matches[1] + 1);
                }
            }

            foreach ([
                ['title' => '[Demo] プロジェクト別カラー確認', 'status' => 'TODO'],
                ['title' => '[Demo] プロジェクト切替テスト', 'status' => 'IN_PROGRESS'],
            ] as $sample) {
                if ($project->tickets()->where('title', $sample['title'])->exists()) {
                    continue;
                }
                Ticket::query()->create([
                    'project_id' => $project->id,
                    'issue_key' => sprintf('%s-%02d', $project->project_key, $next++),
                    'title' => $sample['title'],
                    'description' => 'プレビュー用のサンプルチケットです。',
                    'status' => $sample['status'],
                    'priority' => 'MEDIUM',
                    'position' => $project->tickets()->where('status', $sample['status'])->max('position') + 1,
                ]);
            }
            $project->forceFill(['next_ticket_number' => $next])->save();
        });
    }
}
