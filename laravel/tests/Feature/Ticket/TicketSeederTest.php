<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Database\Seeders\TicketSeeder;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class TicketSeederTest extends TestCase
{
    use RefreshDatabase;

    public function test_seeding_keeps_existing_issue_keys_and_starts_new_samples_at_the_next_number(): void
    {
        $project = Project::query()->where('name', 'General')->firstOrFail();
        $project->forceFill(['project_key' => 'ABC', 'next_ticket_number' => 6])->save();
        $existingSample = Ticket::factory()->create([
            'project_id' => $project->id,
            'issue_key' => 'ABC-41',
            'title' => 'ログインAPIおよびJWTトークン処理の連携',
        ]);
        $existingTicket = Ticket::factory()->create([
            'project_id' => $project->id,
            'issue_key' => 'ABC-42',
            'title' => 'Existing work',
        ]);

        app(TicketSeeder::class)->run();

        $this->assertSame('ABC-41', $existingSample->fresh()->issue_key);
        $this->assertSame('ABC-42', $existingTicket->fresh()->issue_key);
        $this->assertDatabaseHas('tickets', [
            'project_id' => $project->id,
            'title' => 'JiraスタイルかんばんボードのUI実装',
            'issue_key' => 'ABC-43',
        ]);
        $this->assertSame(47, (int) $project->fresh()->next_ticket_number);
    }

    public function test_reseeding_does_not_change_existing_keys_or_reset_the_next_number(): void
    {
        $project = Project::query()->where('name', 'General')->firstOrFail();
        $project->forceFill(['project_key' => 'ABC', 'next_ticket_number' => 8])->save();
        $existing = Ticket::factory()->create([
            'project_id' => $project->id,
            'issue_key' => 'ABC-07',
            'title' => 'ログインAPIおよびJWTトークン処理の連携',
        ]);

        $seeder = app(TicketSeeder::class);
        $seeder->run();
        $keysAfterFirstRun = $project->tickets()->orderBy('id')->pluck('issue_key')->all();
        $nextNumberAfterFirstRun = (int) $project->fresh()->next_ticket_number;

        $seeder->run();

        $this->assertSame('ABC-07', $existing->fresh()->issue_key);
        $this->assertSame($keysAfterFirstRun, $project->tickets()->orderBy('id')->pluck('issue_key')->all());
        $this->assertSame($nextNumberAfterFirstRun, (int) $project->fresh()->next_ticket_number);
        $this->assertSame(5, $project->tickets()->count());
    }

    public function test_deleting_a_ticket_does_not_reuse_its_number(): void
    {
        app(TicketSeeder::class)->run();

        $project = Project::query()->where('name', 'General')->firstOrFail();
        $user = User::query()->where('email', 'jihoon@example.com')->firstOrFail();
        $deletedTicket = $project->tickets()->where('issue_key', 'LIKE', $project->project_key.'-%')
            ->orderByDesc('id')
            ->firstOrFail();
        $deletedNumber = (int) substr($deletedTicket->issue_key, strlen($project->project_key) + 1);
        $deletedTicket->delete();

        $this->actingAs($user)->postJson('/api/tickets', [
            'project_id' => $project->id,
            'title' => 'Created after deletion',
        ])->assertCreated()
            ->assertJsonPath('data.issue_key', sprintf('%s-%02d', $project->project_key, $deletedNumber + 1));
    }
}
