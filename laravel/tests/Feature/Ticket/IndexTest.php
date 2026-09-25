<?php

namespace Tests\Feature\Ticket;

use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class IndexTest extends TestCase
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

    public function test_チケット一覧を取得できる(): void
    {
        $firstTicket = Ticket::factory()->create();
        $secondTicket = Ticket::factory()->create();
        $thirdTicket = Ticket::factory()->create();

        $response = $this->getJson('/api/tickets');

        $response
            ->assertOk()
            ->assertJsonCount(3, 'data')
            ->assertJsonPath('data.0.id', (string) $firstTicket->id)
            ->assertJsonPath('data.1.id', (string) $secondTicket->id)
            ->assertJsonPath('data.2.id', (string) $thirdTicket->id);
    }
}