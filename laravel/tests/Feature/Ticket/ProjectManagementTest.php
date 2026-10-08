<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Event;
use Tests\Feature\Ticket\Concerns\UsesGeneralProject;
use Tests\TestCase;

class ProjectManagementTest extends TestCase
{
    use RefreshDatabase;
    use UsesGeneralProject;

    public function test_project_list_is_limited_to_members_and_admins_can_create_projects(): void
    {
        $member = User::factory()->create();
        $project = Project::factory()->create();
        $this->addProjectMember($project, $member, permission: 'read');
        Project::factory()->create();

        $this->actingAs($member)
            ->getJson('/api/projects')
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.name', $project->name);

        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();
        $this->actingAs($admin)
            ->postJson('/api/projects', ['name' => 'Admin Project'])
            ->assertCreated()
            ->assertJsonPath('data.name', 'Admin Project')
            ->assertJson(fn ($json) => $json
                ->whereType('data.project_key', 'string')
                ->etc());

        $created = Project::query()->where('name', 'Admin Project')->firstOrFail();
        $this->assertMatchesRegularExpression('/^[A-Z]{3}$/', $created->project_key);

        $this->getJson('/api/projects')->assertJsonCount(4, 'data');
    }

    public function test_project_creation_retries_when_another_insert_claims_the_generated_key(): void
    {
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();
        $existing = Project::factory()->create();
        $existingKey = $existing->project_key;
        $collisions = 0;
        $event = 'eloquent.creating: '.Project::class;

        // Force a collision after the model checks for existing keys, simulating a race.
        Event::listen($event, function (Project $candidate) use (&$collisions, $existingKey) {
            if ($collisions++ === 0) {
                $candidate->project_key = $existingKey;
            }
        });

        try {
            $this->actingAs($admin)
                ->postJson('/api/projects', ['name' => 'Retried Project'])
                ->assertCreated()
                ->assertJsonPath('data.name', 'Retried Project');

            $created = Project::query()->where('name', 'Retried Project')->firstOrFail();
            $this->assertNotSame($existingKey, $created->project_key);
            $this->assertMatchesRegularExpression('/^[A-Z]{3}$/', $created->project_key);
            $this->assertSame(2, $collisions);
            $this->assertSame($existingKey, $existing->fresh()->project_key);
        } finally {
            Event::forget($event);
            Project::clearBootedModels();
        }
    }

    public function test_project_creation_stops_after_five_unique_key_collisions(): void
    {
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();
        $existing = Project::factory()->create();
        $attempts = 0;
        $event = 'eloquent.creating: '.Project::class;

        Event::listen($event, function (Project $candidate) use (&$attempts, $existing) {
            $attempts++;
            $candidate->project_key = $existing->project_key;
        });

        try {
            $this->actingAs($admin)->postJson('/api/projects', ['name' => 'Always Collides'])
                ->assertStatus(500);

            $this->assertSame(5, $attempts);
            $this->assertDatabaseMissing('projects', ['name' => 'Always Collides']);
        } finally {
            Event::forget($event);
            Project::clearBootedModels();
        }
    }

    public function test_project_creation_and_changes_are_admin_only(): void
    {
        $member = User::factory()->create();
        $project = Project::factory()->create();
        $this->addProjectMember($project, $member, role: 'leader', permission: 'write');

        $this->actingAs($member)
            ->postJson('/api/projects', ['name' => 'Not allowed'])
            ->assertForbidden();

        $this->patchJson("/api/projects/{$project->id}", ['name' => 'Not allowed'])
            ->assertForbidden();
        $this->deleteJson("/api/projects/{$project->id}")->assertForbidden();

        $this->getJson("/api/projects/{$project->id}")
            ->assertOk()
            ->assertJsonPath('data.name', $project->name);
    }

    public function test_project_key_does_not_change_when_project_is_renamed(): void
    {
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();
        $project = Project::factory()->create();
        $key = $project->project_key;

        $this->actingAs($admin)
            ->patchJson("/api/projects/{$project->id}", [
                'name' => 'Renamed Project',
                'project_key' => 'NEW',
            ])
            ->assertOk()
            ->assertJsonPath('data.name', 'Renamed Project')
            ->assertJsonPath('data.project_key', $key);

        $this->assertSame($key, $project->refresh()->project_key);
    }

    public function test_project_leader_can_add_update_and_remove_members(): void
    {
        $project = Project::factory()->create();
        $leader = User::factory()->create();
        $newMember = User::factory()->create();
        $this->addProjectMember($project, $leader, role: 'leader', permission: 'read');
        $this->actingAs($leader);

        $this->postJson("/api/projects/{$project->id}/members", [
            'email' => $newMember->email,
            'role' => 'member',
            'permission' => 'read',
        ])
            ->assertCreated()
            ->assertJsonPath('data.id', (string) $newMember->id)
            ->assertJsonPath('data.role', 'member')
            ->assertJsonPath('data.permission', 'read');

        $this->getJson("/api/projects/{$project->id}/members")
            ->assertOk()
            ->assertJsonCount(2, 'data');

        $this->patchJson("/api/projects/{$project->id}/members/{$newMember->id}", [
            'role' => 'member',
            'permission' => 'write',
        ])
            ->assertOk()
            ->assertJsonPath('data.permission', 'write');

        $this->deleteJson("/api/projects/{$project->id}/members/{$newMember->id}")
            ->assertNoContent();

        $this->assertDatabaseMissing('project_members', [
            'project_id' => $project->id,
            'user_id' => $newMember->id,
        ]);
    }

    public function test_project_member_cannot_manage_members_and_admin_can(): void
    {
        $project = Project::factory()->create();
        $member = User::factory()->create();
        $newMember = User::factory()->create();
        $this->addProjectMember($project, $member, permission: 'write');
        $this->actingAs($member)
            ->postJson("/api/projects/{$project->id}/members", [
                'email' => $newMember->email,
                'role' => 'member',
                'permission' => 'read',
            ])
            ->assertForbidden();

        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();
        $this->actingAs($admin)
            ->postJson("/api/projects/{$project->id}/members", [
                'email' => $newMember->email,
                'role' => 'member',
                'permission' => 'write',
            ])
            ->assertCreated()
            ->assertJsonPath('data.role', 'member');
    }

    public function test_project_leader_can_transfer_ownership_without_changing_ticket_permissions(): void
    {
        $project = Project::factory()->create();
        $leader = User::factory()->create();
        $nextLeader = User::factory()->create();
        $this->addProjectMember($project, $leader, role: 'leader', permission: 'read');
        $this->addProjectMember($project, $nextLeader, role: 'member', permission: 'write');

        $this->actingAs($leader)
            ->postJson("/api/projects/{$project->id}/members/{$nextLeader->id}/transfer-leader")
            ->assertOk()
            ->assertJsonPath('data.role', 'leader')
            ->assertJsonPath('data.permission', 'write');

        $this->assertDatabaseHas('project_members', [
            'project_id' => $project->id,
            'user_id' => $leader->id,
            'role' => 'member',
            'permission' => 'read',
        ]);
        $this->assertDatabaseHas('project_members', [
            'project_id' => $project->id,
            'user_id' => $nextLeader->id,
            'role' => 'leader',
            'permission' => 'write',
        ]);
        $this->assertSame(1, $project->members()->wherePivot('role', 'leader')->count());

        $this->postJson("/api/projects/{$project->id}/members/{$leader->id}/transfer-leader")
            ->assertForbidden();
        $this->actingAs($nextLeader)
            ->postJson("/api/projects/{$project->id}/members/{$nextLeader->id}/transfer-leader")
            ->assertOk();
    }

    public function test_leader_role_cannot_be_changed_indirectly_or_removed(): void
    {
        $project = Project::factory()->create();
        $leader = User::factory()->create();
        $member = User::factory()->create();
        $outsider = User::factory()->create();
        $this->addProjectMember($project, $leader, role: 'leader', permission: 'write');
        $this->addProjectMember($project, $member, role: 'member', permission: 'read');

        $this->actingAs($leader)
            ->postJson("/api/projects/{$project->id}/members", [
                'email' => $outsider->email,
                'role' => 'leader',
                'permission' => 'write',
            ])->assertUnprocessable();

        $this->patchJson("/api/projects/{$project->id}/members/{$member->id}", [
            'role' => 'leader',
            'permission' => 'write',
        ])->assertUnprocessable();

        $this->patchJson("/api/projects/{$project->id}/members/{$leader->id}", [
            'role' => 'member',
            'permission' => 'write',
        ])->assertStatus(409);

        $this->deleteJson("/api/projects/{$project->id}/members/{$leader->id}")
            ->assertStatus(409);

        $this->postJson("/api/projects/{$project->id}/members/{$outsider->id}/transfer-leader")
            ->assertNotFound();

        $this->assertSame(1, $project->members()->wherePivot('role', 'leader')->count());
    }

    public function test_non_leader_cannot_transfer_project_leadership(): void
    {
        $project = Project::factory()->create();
        $leader = User::factory()->create();
        $member = User::factory()->create();
        $this->addProjectMember($project, $leader, role: 'leader', permission: 'write');
        $this->addProjectMember($project, $member, role: 'member', permission: 'write');

        $this->actingAs($member)
            ->postJson("/api/projects/{$project->id}/members/{$member->id}/transfer-leader")
            ->assertForbidden();

        $this->assertDatabaseHas('project_members', [
            'project_id' => $project->id,
            'user_id' => $leader->id,
            'role' => 'leader',
        ]);
    }

    public function test_projects_with_tickets_cannot_be_deleted(): void
    {
        $project = Project::factory()->create();
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();
        Ticket::factory()->create(['project_id' => $project->id]);

        $this->actingAs($admin)
            ->deleteJson("/api/projects/{$project->id}")
            ->assertStatus(409);

        $this->assertDatabaseHas('projects', ['id' => $project->id]);
    }
}
