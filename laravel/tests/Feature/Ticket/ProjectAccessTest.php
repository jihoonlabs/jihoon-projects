<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\Feature\Ticket\Concerns\UsesGeneralProject;
use Tests\TestCase;

class ProjectAccessTest extends TestCase
{
    use RefreshDatabase;
    use UsesGeneralProject;

    public function test_read_member_can_view_tickets_and_post_comments_but_cannot_change_tickets(): void
    {
        $user = User::factory()->create();
        $project = $this->addToGeneralProject($user, permission: 'read');
        $ticket = Ticket::factory()->create(['project_id' => $project->id]);

        $this->actingAs($user)
            ->getJson('/api/tickets')
            ->assertOk()
            ->assertJsonCount(1, 'data');

        $this->getJson("/api/tickets/{$ticket->id}")->assertOk();
        $this->getJson("/api/tickets/{$ticket->id}/comments")->assertOk();
        $this->postJson("/api/tickets/{$ticket->id}/comments", ['body' => 'A note'])
            ->assertCreated();

        $this->patchJson("/api/tickets/{$ticket->id}", ['status' => 'DONE'])
            ->assertForbidden();
        $this->deleteJson("/api/tickets/{$ticket->id}")->assertForbidden();
        $this->postJson('/api/tickets', [
            'project_id' => $project->id,
            'title' => 'Not allowed',
        ])->assertForbidden();
    }

    public function test_non_member_cannot_read_project_tickets_or_comments(): void
    {
        $project = Project::factory()->create();
        $ticket = Ticket::factory()->create(['project_id' => $project->id]);
        $user = User::factory()->create();

        $this->actingAs($user)
            ->getJson('/api/tickets')
            ->assertOk()
            ->assertJsonCount(0, 'data');

        $this->getJson("/api/tickets/{$ticket->id}")->assertForbidden();
        $this->getJson("/api/tickets/{$ticket->id}/comments")->assertForbidden();
        $this->postJson("/api/tickets/{$ticket->id}/comments", ['body' => 'No access'])
            ->assertForbidden();
    }

    public function test_write_member_can_assign_only_project_members(): void
    {
        $project = Project::factory()->create();
        $writer = User::factory()->create();
        $assignee = User::factory()->create();
        $outsider = User::factory()->create();
        $this->addProjectMember($project, $writer, permission: 'write');
        $this->addProjectMember($project, $assignee, permission: 'read');
        $ticket = Ticket::factory()->create([
            'project_id' => $project->id,
            'assignee_id' => null,
        ]);

        $this->actingAs($writer)
            ->patchJson("/api/tickets/{$ticket->id}", ['assignee_id' => $assignee->id])
            ->assertOk()
            ->assertJsonPath('data.assignee.id', $assignee->id);

        $this->patchJson("/api/tickets/{$ticket->id}", ['assignee_id' => $outsider->id])
            ->assertUnprocessable();

        $this->assertDatabaseHas('tickets', [
            'id' => $ticket->id,
            'assignee_id' => $assignee->id,
        ]);
    }

    public function test_admin_can_access_and_change_tickets_without_project_membership(): void
    {
        $project = Project::factory()->create();
        $ticket = Ticket::factory()->create(['project_id' => $project->id]);
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();

        $this->actingAs($admin)
            ->getJson('/api/tickets')
            ->assertOk()
            ->assertJsonCount(1, 'data');

        $this->patchJson("/api/tickets/{$ticket->id}", ['status' => 'DONE'])
            ->assertOk();
    }

    public function test_admin_can_delete_another_users_comment_but_cannot_edit_it(): void
    {
        $project = Project::factory()->create();
        $author = User::factory()->create();
        $admin = User::factory()->create();
        $admin->forceFill(['role' => 'admin'])->save();
        $ticket = Ticket::factory()->create(['project_id' => $project->id]);
        $comment = $ticket->comments()->make(['body' => 'Keep authorship']);
        $comment->user()->associate($author);
        $comment->save();

        $this->actingAs($admin)
            ->patchJson("/api/tickets/{$ticket->id}/comments/{$comment->id}", ['body' => 'Changed'])
            ->assertForbidden();

        $this->deleteJson("/api/tickets/{$ticket->id}/comments/{$comment->id}")
            ->assertNoContent();
    }
}
