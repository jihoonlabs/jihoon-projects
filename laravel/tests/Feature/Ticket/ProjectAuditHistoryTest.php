<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Tests\TestCase;

class ProjectAuditHistoryTest extends TestCase
{
    use RefreshDatabase;

    public function test_creation_and_rename_preserve_project_identity_and_actor(): void
    {
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();

        $this->actingAs($admin)->postJson('/api/projects', ['name' => 'Original'])
            ->assertCreated();
        $project = Project::query()->where('name', 'Original')->firstOrFail();

        $this->patchJson("/api/projects/{$project->id}", ['name' => 'Updated'])
            ->assertOk();

        $events = DB::table('project_audit_events')->where('project_id', $project->id)
            ->orderBy('id')->get();
        $this->assertSame(['project.created', 'project.renamed'], $events->pluck('action')->all());
        $this->assertSame($project->project_key, $events->first()->project_key);
        $this->assertSame($admin->id, $events->last()->actor_id);
        $renamed = json_decode($events->last()->snapshot, true, 512, JSON_THROW_ON_ERROR);
        $this->assertSame('Original', $renamed['previous_name']);
        $this->assertSame('Updated', $renamed['name']);
    }

    public function test_deleting_empty_project_retains_identity_in_ledger(): void
    {
        $project = Project::factory()->create();
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();

        $this->actingAs($admin)->deleteJson("/api/projects/{$project->id}")
            ->assertNoContent();

        $this->assertDatabaseMissing('projects', ['id' => $project->id]);
        $this->assertDatabaseHas('project_audit_events', [
            'project_id' => $project->id,
            'project_key' => $project->project_key,
            'actor_id' => $admin->id,
            'action' => 'project.deleted',
        ]);
    }

    public function test_delete_with_tickets_is_rejected_without_audit_event(): void
    {
        $project = Project::factory()->create();
        Ticket::factory()->create(['project_id' => $project->id]);
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();

        $this->actingAs($admin)->deleteJson("/api/projects/{$project->id}")
            ->assertStatus(409);

        $this->assertDatabaseHas('projects', ['id' => $project->id]);
        $this->assertDatabaseCount('project_audit_events', 0);
    }

    public function test_normal_user_cannot_rename_or_delete_or_log_admin_events(): void
    {
        $project = Project::factory()->create();
        $user = User::factory()->create();
        $this->actingAs($user)->patchJson("/api/projects/{$project->id}", [
            'name' => 'Forbidden',
        ])->assertForbidden();
        $this->deleteJson("/api/projects/{$project->id}")->assertForbidden();

        $this->assertDatabaseCount('project_audit_events', 0);
    }
}
