<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ProjectRelationshipTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_ticket_and_project_relationships_preserve_membership_pivot_data(): void
    {
        $project = Project::factory()->create();
        $user = User::factory()->create();
        $ticket = Ticket::factory()->create(['project_id' => $project->id]);
        $project->members()->attach($user, [
            'role' => 'leader',
            'permission' => 'write',
        ]);

        $this->assertTrue($ticket->project->is($project));
        $this->assertTrue($project->tickets->contains($ticket));
        $this->assertTrue($user->projects->contains($project));
        $this->assertSame('leader', $user->projects->first()->pivot->role);
        $this->assertSame('write', $user->projects->first()->pivot->permission);
    }
}
