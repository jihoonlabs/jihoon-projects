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
        $this->patchJson("/api/projects/{$project->id}", ['name' => 'Updated'])
            ->assertOk();

        $events = DB::table('project_audit_events')->where('project_id', $project->id)
            ->orderBy('id')->get();
        $this->assertSame(['project.created', 'project.renamed'], $events->pluck('action')->all());
        $this->assertSame($project->project_key, $events->first()->project_key);
        $this->assertSame($admin->id, $events->first()->actor_id);
        $this->assertSame($admin->name, $events->first()->actor_name);
        $created = json_decode($events->first()->snapshot, true, 512, JSON_THROW_ON_ERROR);
        $this->assertSame(['name' => 'Original'], $created);
        $this->assertSame($admin->id, $events->last()->actor_id);
        $this->assertSame($admin->name, $events->last()->actor_name);
        $renamed = json_decode($events->last()->snapshot, true, 512, JSON_THROW_ON_ERROR);
        $this->assertSame('Original', $renamed['previous_name']);
        $this->assertSame('Updated', $renamed['name']);
    }

    public function test_active_user_creation_registers_leader_and_audit_in_one_operation(): void
    {
        $creator = User::factory()->create();

        $this->actingAs($creator)
            ->postJson('/api/projects', ['name' => 'Team Project'])
            ->assertCreated()
            ->assertJsonPath('data.created_by', (string) $creator->id);

        $project = Project::query()->where('name', 'Team Project')->firstOrFail();
        $this->assertSame($creator->id, (int) $project->created_by);
        $this->assertDatabaseHas('project_members', [
            'project_id' => $project->id,
            'user_id' => $creator->id,
            'role' => 'leader',
            'permission' => 'write',
        ]);
        $this->assertDatabaseHas('project_audit_events', [
            'project_id' => $project->id,
            'actor_id' => $creator->id,
            'action' => 'project.created',
        ]);
    }

    public function test_project_and_initial_membership_roll_back_when_creation_audit_fails(): void
    {
        $creator = User::factory()->create();
        $this->failAuditAction('project.created');

        $this->actingAs($creator)
            ->postJson('/api/projects', ['name' => 'Must Roll Back'])
            ->assertServerError();

        $this->assertDatabaseMissing('projects', ['name' => 'Must Roll Back']);
        $this->assertDatabaseMissing('project_members', ['user_id' => $creator->id]);
        $this->assertDatabaseCount('project_audit_events', 0);
    }

    public function test_archive_rolls_back_when_archive_audit_fails(): void
    {
        $project = Project::factory()->create();
        $leader = User::factory()->create();
        $project->members()->attach($leader->id, ['role' => 'leader', 'permission' => 'write']);
        $this->failAuditAction('project.archived');

        $this->actingAs($leader)
            ->postJson("/api/projects/{$project->id}/archive")
            ->assertServerError();

        $this->assertNull($project->fresh()->archived_at);
        $this->assertDatabaseCount('project_audit_events', 0);
    }

    public function test_restore_rolls_back_when_restore_audit_fails(): void
    {
        $project = Project::factory()->create(['archived_at' => now()]);
        $leader = User::factory()->create();
        $project->members()->attach($leader->id, ['role' => 'leader', 'permission' => 'write']);
        $this->failAuditAction('project.restored');

        $this->actingAs($leader)
            ->postJson("/api/projects/{$project->id}/restore")
            ->assertServerError();

        $this->assertNotNull($project->fresh()->archived_at);
        $this->assertDatabaseCount('project_audit_events', 0);
    }

    public function test_deleting_empty_project_retains_identity_in_ledger(): void
    {
        $project = Project::factory()->create();
        $createdAt = $project->created_at?->toIso8601String();
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

        $event = DB::table('project_audit_events')->where('project_id', $project->id)->first();
        $this->assertSame($admin->id, $event->actor_id);
        $this->assertSame($admin->name, $event->actor_name);
        $deleted = json_decode($event->snapshot, true, 512, JSON_THROW_ON_ERROR);
        $this->assertSame($project->name, $deleted['name']);
        $this->assertSame($createdAt, $deleted['created_at']);
    }

    public function test_deleted_project_key_is_reserved_for_new_projects(): void
    {
        $project = Project::factory()->create();
        $historicalKey = $project->project_key;
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();

        $this->actingAs($admin)->deleteJson("/api/projects/{$project->id}")
            ->assertNoContent();

        // Even an explicit import/factory assignment cannot resurrect a deleted key.
        try {
            Project::factory()->create(['project_key' => $historicalKey]);
            $this->fail('Historical project key should be rejected.');
        } catch (\InvalidArgumentException $exception) {
            $this->assertSame('This project key is permanently reserved.', $exception->getMessage());
        }

        $replacement = Project::factory()->create();
        $this->assertNotSame($historicalKey, $replacement->project_key);
        $this->assertDatabaseHas('project_audit_events', [
            'project_key' => $historicalKey,
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

    private function failAuditAction(string $action): void
    {
        $quotedAction = DB::connection()->getPdo()->quote($action);
        DB::unprepared("CREATE TRIGGER fail_project_audit_event BEFORE INSERT ON project_audit_events WHEN NEW.action = {$quotedAction} BEGIN SELECT RAISE(ABORT, 'forced audit failure'); END;");
    }
}
