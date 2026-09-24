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
            ->assertJsonCount(3)
            ->assertJsonPath('0.id', $firstTicket->id)
            ->assertJsonPath('1.id', $secondTicket->id)
            ->assertJsonPath('2.id', $thirdTicket->id);
    }
}