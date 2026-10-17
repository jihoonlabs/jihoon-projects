<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
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

    public function test_project_search_by_key_and_name_is_limited_to_accessible_projects(): void
    {
        $member = User::factory()->create();
        $visible = Project::factory()->create(['name' => 'Customer Portal']);
        $hidden = Project::factory()->create(['name' => 'Customer Private']);
        $this->addProjectMember($visible, $member, permission: 'read');

        $this->actingAs($member)
            ->getJson('/api/projects?search='.strtolower($visible->project_key))
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.project_key', $visible->project_key);

        $this->getJson('/api/projects?search=Customer')
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.name', 'Customer Portal');

        $this->getJson('/api/projects?search=missing')
            ->assertOk()
            ->assertJsonCount(0, 'data');

        $this->getJson('/api/projects?search='.strtolower($hidden->project_key))
            ->assertOk()
            ->assertJsonCount(0, 'data');

        $this->getJson('/api/projects?search[]='.strtolower($visible->project_key))
            ->assertUnprocessable();
    }

    public function test_project_search_composes_with_archive_filter_without_leaking_other_projects(): void
    {
        $member = User::factory()->create();
        $active = Project::factory()->create(['name' => 'Operations Active']);
        $archived = Project::factory()->create(['name' => 'Operations Archived']);
        $archived->forceFill(['archived_at' => now()])->save();
        $this->addProjectMember($active, $member, permission: 'read');
        $this->addProjectMember($archived, $member, permission: 'read');

        $this->actingAs($member)
            ->getJson('/api/projects?search=Operations')
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.name', $active->name);

        $this->getJson('/api/projects?archived=1&search=Operations')
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.name', $archived->name);
    }

    public function test_project_lookup_by_stable_key_enforces_membership_and_supports_lowercase(): void
    {
        $member = User::factory()->create();
        $visible = Project::factory()->create();
        $hidden = Project::factory()->create();
        $this->addProjectMember($visible, $member, permission: 'read');

        $this->actingAs($member)
            ->getJson('/api/projects/by-key/'.strtolower($visible->project_key))
            ->assertOk()
            ->assertJsonPath('data.id', (string) $visible->id)
            ->assertJsonPath('data.project_key', $visible->project_key);

        $this->getJson('/api/projects/by-key/'.$hidden->project_key)
            ->assertForbidden();

        $this->getJson('/api/projects/by-key/INVALID')
            ->assertNotFound();

        $this->getJson('/api/projects/by-key/999')
            ->assertNotFound();

        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();
        $this->actingAs($admin)
            ->getJson('/api/projects/by-key/'.$hidden->project_key)
            ->assertOk()
            ->assertJsonPath('data.id', (string) $hidden->id);
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

    public function test_active_users_can_create_projects_but_changes_are_admin_only(): void
    {
        $member = User::factory()->create();
        $project = Project::factory()->create();
        $this->addProjectMember($project, $member, role: 'leader', permission: 'write');

        $this->actingAs($member)
            ->postJson('/api/projects', ['name' => 'User-created project'])
            ->assertCreated();
        $created = Project::query()->where('name', 'User-created project')->firstOrFail();
        $this->assertSame($member->id, (int) $created->created_by);
        $this->assertSame('leader', $created->members()->firstOrFail()->pivot->role);

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

    public function test_leadership_transfer_rejects_projects_without_exactly_one_current_leader(): void
    {
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();
        $emptyLeadership = Project::factory()->create();
        $member = User::factory()->create();
        $this->addProjectMember($emptyLeadership, $member, role: 'member', permission: 'write');
        $multipleLeaders = Project::factory()->create();
        $firstLeader = User::factory()->create();
        $secondLeader = User::factory()->create();
        $this->addProjectMember($multipleLeaders, $firstLeader, role: 'leader', permission: 'read');
        $this->addProjectMember($multipleLeaders, $secondLeader, role: 'leader', permission: 'write');

        $this->actingAs($admin)
            ->postJson("/api/projects/{$emptyLeadership->id}/members/{$member->id}/transfer-leader")
            ->assertStatus(409);
        $this->postJson("/api/projects/{$multipleLeaders->id}/members/{$secondLeader->id}/transfer-leader")
            ->assertStatus(409);

        $this->assertSame(0, $emptyLeadership->members()->wherePivot('role', 'leader')->count());
        $this->assertSame(2, $multipleLeaders->members()->wherePivot('role', 'leader')->count());
    }

    public function test_project_leader_can_archive_completed_project_and_restore_it(): void
    {
        $project = Project::factory()->create();
        $leader = User::factory()->create();
        $this->addProjectMember($project, $leader, role: 'leader', permission: 'write');
        $ticket = Ticket::factory()->create(['project_id' => $project->id, 'status' => 'DONE']);
        $originalKey = $project->project_key;

        $this->actingAs($leader)
            ->postJson("/api/projects/{$project->id}/archive")
            ->assertOk()
            ->assertJson(fn ($json) => $json->whereType('data.archived_at', 'string')->etc());
        $this->postJson("/api/projects/{$project->id}/archive")->assertOk();

        $this->assertNotNull($project->fresh()->archived_at);
        $this->getJson('/api/projects')->assertOk()->assertJsonCount(0, 'data');
        $this->getJson('/api/projects?archived=1')
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.project_key', $originalKey);
        $this->getJson("/api/projects/{$project->id}")
            ->assertOk()
            ->assertJsonPath('data.project_key', $originalKey);

        $this->postJson("/api/projects/{$project->id}/restore")
            ->assertOk()
            ->assertJsonPath('data.archived_at', null);
        $this->postJson("/api/projects/{$project->id}/restore")->assertOk();
        $this->getJson('/api/projects')->assertOk()->assertJsonCount(1, 'data');
        $this->assertDatabaseHas('tickets', ['id' => $ticket->id, 'project_id' => $project->id]);
        $this->assertSame(
            ['project.archived', 'project.restored'],
            DB::table('project_audit_events')->where('project_id', $project->id)->orderBy('id')->pluck('action')->all()
        );
    }

    public function test_project_with_unfinished_ticket_cannot_be_archived(): void
    {
        $project = Project::factory()->create();
        $leader = User::factory()->create();
        $this->addProjectMember($project, $leader, role: 'leader', permission: 'write');
        Ticket::factory()->create(['project_id' => $project->id, 'status' => 'IN_PROGRESS']);

        $this->actingAs($leader)
            ->postJson("/api/projects/{$project->id}/archive")
            ->assertStatus(409);

        $this->assertNull($project->fresh()->archived_at);
    }

    public function test_regular_member_cannot_archive_or_restore_project(): void
    {
        $project = Project::factory()->create();
        $member = User::factory()->create();
        $this->addProjectMember($project, $member, role: 'member', permission: 'write');
        $this->actingAs($member)
            ->postJson("/api/projects/{$project->id}/archive")->assertForbidden();

        $project->forceFill(['archived_at' => now()])->save();
        $this->postJson("/api/projects/{$project->id}/restore")->assertForbidden();
        $this->assertNotNull($project->fresh()->archived_at);
    }

    public function test_archived_project_rejects_ticket_creation_and_allows_restoration(): void
    {
        $project = Project::factory()->create();
        $leader = User::factory()->create();
        $this->addProjectMember($project, $leader, role: 'leader', permission: 'write');
        $project->forceFill(['archived_at' => now()])->save();

        $this->actingAs($leader)
            ->postJson('/api/tickets', [
                'project_id' => $project->id,
                'title' => 'Must not be created',
            ])->assertStatus(409);
        $this->assertDatabaseMissing('tickets', [
            'project_id' => $project->id,
            'title' => 'Must not be created',
        ]);

        $this->postJson("/api/projects/{$project->id}/restore")->assertOk();
        $this->postJson('/api/tickets', [
            'project_id' => $project->id,
            'title' => 'Created after restore',
        ])->assertCreated();
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
