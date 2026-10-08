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
        $this->assertDatabaseHas('project_members', [
            'project_id' => $created->id,
            'user_id' => $admin->id,
            'role' => 'leader',
            'permission' => 'write',
        ]);

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

    public function test_any_user_can_create_project_but_only_admin_can_change_or_delete_it(): void
    {
        $member = User::factory()->create();
        $project = Project::factory()->create();
        $this->addProjectMember($project, $member, role: 'leader', permission: 'write');

        $this->actingAs($member)
            ->postJson('/api/projects', ['name' => 'Member Project'])
            ->assertCreated()
            ->assertJsonPath('data.name', 'Member Project');

        $created = Project::query()->where('name', 'Member Project')->firstOrFail();
        $this->assertDatabaseHas('project_members', [
            'project_id' => $created->id,
            'user_id' => $member->id,
            'role' => 'leader',
            'permission' => 'write',
        ]);

        $this->patchJson("/api/projects/{$project->id}", ['name' => 'Not allowed'])
            ->assertForbidden();
        $this->deleteJson("/api/projects/{$project->id}")->assertForbidden();

        $this->getJson("/api/projects/{$project->id}")
            ->assertOk()
            ->assertJsonPath('data.name', $project->name);
    }

    public function test_guest_cannot_create_a_project_or_membership(): void
    {
        $this->postJson('/api/projects', ['name' => 'Guest attempt'])
            ->assertUnauthorized();

        $this->assertDatabaseMissing('projects', ['name' => 'Guest attempt']);
    }

    public function test_legacy_projects_have_unknown_creator_without_guessing_from_leader(): void
    {
        $legacy = Project::factory()->create();
        $leader = User::factory()->create();
        $this->addProjectMember($legacy, $leader, role: 'leader', permission: 'write');

        $this->assertNull($legacy->refresh()->created_by);
        $this->actingAs($leader)->getJson("/api/projects/{$legacy->id}")
            ->assertOk()
            ->assertJsonPath('data.created_by', null);
    }

    public function test_project_creator_is_persisted_and_cannot_be_spoofed_or_changed(): void
    {
        $creator = User::factory()->create();
        $other = User::factory()->create();
        $this->actingAs($creator)->postJson('/api/projects', [
            'name' => 'Creator identity',
            'created_by' => $other->id,
        ])->assertCreated()->assertJsonPath('data.created_by', (string) $creator->id);

        $project = Project::query()->where('name', 'Creator identity')->firstOrFail();
        $this->assertSame($creator->id, (int) $project->created_by);

        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();
        $this->actingAs($admin)->patchJson("/api/projects/{$project->id}", [
            'name' => 'Renamed by admin',
            'created_by' => $other->id,
        ])->assertOk()->assertJsonPath('data.created_by', (string) $creator->id);

        $this->assertSame($creator->id, (int) $project->refresh()->created_by);
    }

    public function test_project_creator_does_not_change_when_leader_membership_changes(): void
    {
        $creator = User::factory()->create();
        $nextLeader = User::factory()->create();

        $this->actingAs($creator)->postJson('/api/projects', [
            'name' => 'Transfer independent ownership',
        ])->assertCreated();

        $project = Project::query()->where('name', 'Transfer independent ownership')->firstOrFail();
        $project->members()->updateExistingPivot($creator->id, ['role' => 'member']);
        $project->members()->attach($nextLeader->id, [
            'role' => 'leader',
            'permission' => 'write',
        ]);

        $this->assertSame($creator->id, (int) $project->refresh()->created_by);
        $this->assertSame('member', $project->members()->where('users.id', $creator->id)->firstOrFail()->pivot->role);
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
                'role' => 'leader',
                'permission' => 'write',
            ])
            ->assertCreated()
            ->assertJsonPath('data.role', 'leader');
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
