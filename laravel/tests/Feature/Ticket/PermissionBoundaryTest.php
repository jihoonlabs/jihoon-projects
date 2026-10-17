<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\Feature\Ticket\Concerns\UsesGeneralProject;
use Tests\TestCase;

class PermissionBoundaryTest extends TestCase
{
    use RefreshDatabase;
    use UsesGeneralProject;

    public static function ticketOperations(): array
    {
        return [['create'], ['update'], ['move'], ['delete']];
    }

    // Inject the membership change between the initial check and locked mutation.
    // This deterministic boundary test does not simulate a database lock wait.
    private function afterProjectLock(\Closure $change): \Closure
    {
        $level = DB::transactionLevel();
        $called = false;
        Project::retrieved(function (Project $project) use ($change, $level, &$called) {
            if (! $called && DB::transactionLevel() > $level) {
                $called = true;
                $change($project);
            }
        });

        return function () use (&$called) {
            return $called;
        };
    }

    #[DataProvider('ticketOperations')]
    public function test_revoked_writer_cannot_mutate_after_lock(string $operation): void
    {
        $user = User::factory()->create(['status' => 'active']);
        $project = $this->addToGeneralProject($user);
        $ticket = Ticket::factory()->create(['title' => 'Before']);
        $before = $ticket->fresh()->getAttributes();
        $projectBefore = $project->fresh()->getAttributes();
        $injected = $this->afterProjectLock(fn (Project $locked) => $locked->members()->updateExistingPivot($user->id, ['permission' => 'read'])
        );
        $this->actingAs($user);
        $response = match ($operation) {
            'create' => $this->postJson('/api/tickets', ['project_id' => $project->id, 'title' => 'New']),
            'update' => $this->patchJson("/api/tickets/{$ticket->id}", ['title' => 'After']),
            'move' => $this->patchJson("/api/tickets/{$ticket->id}/move", ['status' => 'DONE', 'position' => 0, 'board_version' => $project->board_version]),
            'delete' => $this->deleteJson("/api/tickets/{$ticket->id}"),
        };
        $this->assertTrue($injected());
        $response->assertForbidden();
        $this->assertDatabaseCount('tickets', 1);
        $this->assertSame($before, $ticket->fresh()->getAttributes());
        $this->assertSame($projectBefore, $project->fresh()->getAttributes());
    }

    public static function assignmentOperations(): array
    {
        return [['create'], ['update']];
    }

    #[DataProvider('assignmentOperations')]
    public function test_removed_assignee_is_rejected_after_lock(string $operation): void
    {
        $writer = User::factory()->create(['status' => 'active']);
        $assignee = User::factory()->create();
        $project = $this->addToGeneralProject($writer);
        $this->addProjectMember($project, $assignee);
        $ticket = Ticket::factory()->create();
        $injected = $this->afterProjectLock(fn (Project $locked) => $locked->members()->detach($assignee->id));
        $this->actingAs($writer);
        $input = ['title' => 'Assigned', 'project_id' => $project->id, 'assignee_id' => $assignee->id];
        $response = $operation === 'create'
            ? $this->postJson('/api/tickets', $input)
            : $this->patchJson("/api/tickets/{$ticket->id}", $input);
        $this->assertTrue($injected());
        $response->assertUnprocessable();
        $this->assertDatabaseCount('tickets', 1);
        $this->assertNull($ticket->fresh()->assignee_id);
    }

    public static function commentOperations(): array
    {
        return [['create'], ['update'], ['delete']];
    }

    #[DataProvider('commentOperations')]
    public function test_removed_member_cannot_mutate_comment_after_lock(string $operation): void
    {
        $user = User::factory()->create(['status' => 'active']);
        $this->addToGeneralProject($user, permission: 'read');
        $ticket = Ticket::factory()->create();
        $comment = $ticket->comments()->make(['body' => 'Before']);
        $comment->user()->associate($user);
        $comment->save();
        $injected = $this->afterProjectLock(fn (Project $locked) => $locked->members()->detach($user->id));
        $this->actingAs($user);
        $url = "/api/tickets/{$ticket->id}/comments";
        $response = match ($operation) {
            'create' => $this->postJson($url, ['body' => 'New']),
            'update' => $this->patchJson("$url/{$comment->id}", ['body' => 'After']),
            'delete' => $this->deleteJson("$url/{$comment->id}"),
        };
        $this->assertTrue($injected());
        $response->assertForbidden();
        $this->assertDatabaseCount('ticket_comments', 1);
        $this->assertSame('Before', $comment->fresh()->body);
    }
}
