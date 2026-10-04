<?php

namespace Tests\Feature\Ticket;

use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\Feature\Ticket\Concerns\UsesGeneralProject;
use Tests\TestCase;

class DestroyTest extends TestCase
{
    use RefreshDatabase;
    use UsesGeneralProject;

    protected function setUp(): void
    {
        parent::setUp();

        $user = User::factory()->create([
            'status' => 'active',
        ]);

        $this->actingAs($user);
        $this->addToGeneralProject($user);
    }

    public function test_チケットを削除できる(): void
    {
        $ticket = Ticket::factory()->create();

        $response = $this->deleteJson("/api/tickets/{$ticket->id}");

        $response
            ->assertOk()
            ->assertJsonPath('message', 'Ticket deleted successfully');

        $this->assertDatabaseMissing('tickets', [
            'id' => $ticket->id,
        ]);
    }
}
