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
            ->assertJsonPath('ticket.id', $ticket->id)
            ->assertJsonPath('ticket.status', 'IN_PROGRESS');

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
}