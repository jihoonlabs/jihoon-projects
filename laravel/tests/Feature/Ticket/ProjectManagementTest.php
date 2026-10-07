<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
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
