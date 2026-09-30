<?php

namespace Tests\Feature\Ticket;

use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Http\Middleware\ValidateCsrfToken;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class EnforceCsrfTokenDuringTests extends ValidateCsrfToken
{
    protected function runningUnitTests()
    {
        return false;
    }
}

class CsrfProtectionTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();

        config([
            'sanctum.middleware.validate_csrf_token' => EnforceCsrfTokenDuringTests::class,
        ]);

        $user = User::factory()->create(['status' => 'active']);
        $this->actingAs($user);
    }

    public function test_ticket_status_update_accepts_a_valid_csrf_token(): void
    {
        $ticket = Ticket::factory()->create(['status' => 'TODO']);

        $this->withHeaders([
            'Origin' => 'http://localhost:3000',
            'X-CSRF-TOKEN' => 'session-csrf-token',
        ])
            ->withSession(['_token' => 'session-csrf-token'])
            ->patchJson("/api/tickets/{$ticket->id}", [
                'status' => 'IN_PROGRESS',
            ])
            ->assertOk()
            ->assertJsonPath('data.status', 'IN_PROGRESS');

        $this->assertDatabaseHas('tickets', [
            'id' => $ticket->id,
            'status' => 'IN_PROGRESS',
        ]);
    }

    public function test_ticket_status_update_rejects_a_missing_csrf_token(): void
    {
        $ticket = Ticket::factory()->create(['status' => 'TODO']);

        $this->withHeader('Origin', 'http://localhost:3000')
            ->withSession(['_token' => 'session-csrf-token'])
            ->patchJson("/api/tickets/{$ticket->id}", [
                'status' => 'IN_PROGRESS',
            ])
            ->assertStatus(419);

        $this->assertDatabaseHas('tickets', [
            'id' => $ticket->id,
            'status' => 'TODO',
        ]);
    }
}
