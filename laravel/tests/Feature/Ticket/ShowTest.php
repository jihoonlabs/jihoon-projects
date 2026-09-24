<?php

namespace Tests\Feature\Ticket;

use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ShowTest extends TestCase
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

    public function test_チケット詳細を取得できる(): void
    {
        $ticket = Ticket::factory()->create([
            'title' => '詳細確認チケット',
            'status' => 'IN_PROGRESS',
            'priority' => 'HIGH',
        ]);

        $response = $this->getJson("/api/tickets/{$ticket->id}");

        $response
            ->assertOk()
            ->assertJsonPath('id', $ticket->id)
            ->assertJsonPath('issue_key', $ticket->issue_key)
            ->assertJsonPath('title', '詳細確認チケット')
            ->assertJsonPath('status', 'IN_PROGRESS')
            ->assertJsonPath('priority', 'HIGH');
    }

    public function test_存在しないチケットは取得できない(): void
    {
        $response = $this->getJson('/api/tickets/999999');

        $response->assertNotFound();
    }
}