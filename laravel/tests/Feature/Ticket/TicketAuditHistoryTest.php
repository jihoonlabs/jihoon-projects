<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Tests\Feature\Ticket\Concerns\UsesGeneralProject;
use Tests\TestCase;

class TicketAuditHistoryTest extends TestCase
{
    use RefreshDatabase;
    use UsesGeneralProject;

    public function test_ticket_deletion_saves_a_durable_snapshot_and_actor(): void
    {
        $project = Project::factory()->create();
        $writer = User::factory()->create();
        $this->addProjectMember($project, $writer, permission: 'write');
        $ticket = Ticket::factory()->create([
            'project_id' => $project->id,
            'title' => 'Important work',
            'description' => 'Reason for the task',
            'status' => 'DONE',
        ]);
        $ticketId = $ticket->id;
        $issueKey = $ticket->issue_key;

        $this->actingAs($writer)->deleteJson("/api/tickets/{$ticketId}")->assertOk();

        $this->assertDatabaseMissing('tickets', ['id' => $ticketId]);
        $this->assertDatabaseHas('ticket_audit_events', [
            'project_id' => $project->id,
            'project_key' => $project->project_key,
            'ticket_id' => $ticketId,
            'issue_key' => $issueKey,
            'actor_id' => $writer->id,
            'actor_name' => $writer->name,
            'action' => 'ticket.deleted',
        ]);

        $event = DB::table('ticket_audit_events')->where('ticket_id', $ticketId)->first();
        $this->assertNotNull($event);
        $snapshot = json_decode($event->snapshot, true, 512, JSON_THROW_ON_ERROR);
        $this->assertSame('Important work', $snapshot['title']);
        $this->assertSame('Reason for the task', $snapshot['description']);
        $this->assertSame('DONE', $snapshot['status']);
    }

    public function test_read_only_member_cannot_delete_ticket_or_create_audit_event(): void
    {
        $project = Project::factory()->create();
        $reader = User::factory()->create();
        $this->addProjectMember($project, $reader, permission: 'read');
        $ticket = Ticket::factory()->create(['project_id' => $project->id]);

        $this->actingAs($reader)->deleteJson("/api/tickets/{$ticket->id}")->assertForbidden();

        $this->assertDatabaseHas('tickets', ['id' => $ticket->id]);
        $this->assertDatabaseCount('ticket_audit_events', 0);
    }

    public function test_creating_and_updating_ticket_records_work_history(): void
    {
        $project = Project::factory()->create();
        $writer = User::factory()->create();
        $this->addProjectMember($project, $writer, permission: 'write');

        $response = $this->actingAs($writer)->postJson('/api/tickets', [
            'project_id' => $project->id,
            'title' => 'First task',
        ])->assertCreated();

        $ticketId = $response->json('data.id');
        $this->patchJson("/api/tickets/{$ticketId}", [
            'title' => 'Revised task',
            'status' => 'DONE',
        ])->assertOk();

        $events = DB::table('ticket_audit_events')->where('ticket_id', $ticketId)
            ->orderBy('id')->get();
        $this->assertSame(['ticket.created', 'ticket.updated'], $events->pluck('action')->all());
        $this->assertSame($project->project_key, $events->first()->project_key);
        $this->assertSame($writer->id, $events->last()->actor_id);
        $snapshot = json_decode($events->last()->snapshot, true, 512, JSON_THROW_ON_ERROR);
        $this->assertSame('Revised task', $snapshot['title']);
        $this->assertSame('DONE', $snapshot['status']);
    }

    public function test_read_only_member_cannot_create_audit_events_by_editing(): void
    {
        $project = Project::factory()->create();
        $reader = User::factory()->create();
        $this->addProjectMember($project, $reader, permission: 'read');
        $ticket = Ticket::factory()->create(['project_id' => $project->id]);

        $this->actingAs($reader)->patchJson("/api/tickets/{$ticket->id}", [
            'title' => 'Unauthorized',
        ])->assertForbidden();

        $this->assertDatabaseCount('ticket_audit_events', 0);
    }

    public function test_repeated_deletion_does_not_create_duplicate_audit_events(): void
    {
        $project = Project::factory()->create();
        $writer = User::factory()->create();
        $this->addProjectMember($project, $writer, permission: 'write');
        $ticket = Ticket::factory()->create(['project_id' => $project->id]);

        $this->actingAs($writer)->deleteJson("/api/tickets/{$ticket->id}")->assertOk();
        $this->deleteJson("/api/tickets/{$ticket->id}")->assertNotFound();

        $this->assertDatabaseCount('ticket_audit_events', 1);
    }
}
