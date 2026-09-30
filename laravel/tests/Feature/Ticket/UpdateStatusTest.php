<?php

namespace Tests\Feature\Ticket;

use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class UpdateStatusTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        $user = User::factory()->create([
            'status' => 'active',
        ]);

        $this->actingAs($user);
    }

    public function test_チケットのステータスを更新できる(): void
    {
        $ticket = Ticket::factory()->create([
            'status' => 'TODO',
        ]);

        $response = $this->patchJson("/api/tickets/{$ticket->id}", [
            'status' => 'IN_PROGRESS',
        ]);

        $response
            ->assertOk()
            ->assertJsonPath('data.id', (string) $ticket->id)
            ->assertJsonPath('data.status', 'IN_PROGRESS');

        $this->assertDatabaseHas('tickets', [
            'id' => $ticket->id,
            'status' => 'IN_PROGRESS',
        ]);
    }

    public function test_不正なステータスには更新できない(): void
    {
        $ticket = Ticket::factory()->create([
            'status' => 'TODO',
        ]);

        $response = $this->patchJson("/api/tickets/{$ticket->id}", [
            'status' => 'INVALID',
        ]);

        $response
            ->assertUnprocessable()
            ->assertJsonValidationErrors(['status']);

        $this->assertDatabaseHas('tickets', [
            'id' => $ticket->id,
            'status' => 'TODO',
        ]);
    }

    public function test_チケットの内容を更新できる(): void
    {
        $assignee = User::factory()->create();
        $ticket = Ticket::factory()->create([
            'title' => '更新前',
            'description' => null,
            'status' => 'TODO',
            'priority' => 'MEDIUM',
            'assignee_id' => null,
        ]);

        $response = $this->patchJson("/api/tickets/{$ticket->id}", [
            'title' => '更新後',
            'description' => '説明を更新',
            'status' => 'IN_REVIEW',
            'priority' => 'HIGH',
            'assignee_id' => $assignee->id,
        ]);

        $response
            ->assertOk()
            ->assertJsonPath('data.title', '更新後')
            ->assertJsonPath('data.description', '説明を更新')
            ->assertJsonPath('data.status', 'IN_REVIEW')
            ->assertJsonPath('data.priority', 'HIGH')
            ->assertJsonPath('data.assignee.id', $assignee->id);

        $this->assertDatabaseHas('tickets', [
            'id' => $ticket->id,
            'title' => '更新後',
            'status' => 'IN_REVIEW',
            'priority' => 'HIGH',
            'assignee_id' => $assignee->id,
        ]);
    }

    public function test_編集項目の不正な値は更新できない(): void
    {
        $ticket = Ticket::factory()->create([
            'title' => '更新前',
            'priority' => 'MEDIUM',
            'assignee_id' => null,
        ]);

        $response = $this->patchJson("/api/tickets/{$ticket->id}", [
            'title' => '',
            'priority' => 'URGENT',
            'assignee_id' => 999999,
        ]);

        $response
            ->assertUnprocessable()
            ->assertJsonValidationErrors(['title', 'priority', 'assignee_id']);

        $this->assertDatabaseHas('tickets', [
            'id' => $ticket->id,
            'title' => '更新前',
            'priority' => 'MEDIUM',
            'assignee_id' => null,
        ]);
    }
}
