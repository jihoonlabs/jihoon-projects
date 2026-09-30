<?php

namespace Tests\Feature\Ticket;

use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class AuthenticationTest extends TestCase
{
    use RefreshDatabase;

    public function test_未認証ユーザーはチケット一覧を取得できない(): void
    {
        $response = $this->getJson('/api/tickets');

        $response->assertUnauthorized();
    }

    public function test_停止中のユーザーはチケット一覧を取得できない(): void
    {
        $user = User::factory()->create([
            'status' => 'suspended',
        ]);

        $this->actingAs($user);

        $response = $this->getJson('/api/tickets');

        $response->assertForbidden();
    }

    public function test_未認証ユーザーはチケットを変更できない(): void
    {
        $ticket = Ticket::factory()->create();

        $this->patchJson("/api/tickets/{$ticket->id}", [
            'title' => '変更後',
        ])->assertUnauthorized();

        $this->deleteJson("/api/tickets/{$ticket->id}")
            ->assertUnauthorized();
    }

    public function test_停止中のユーザーはチケットを変更できない(): void
    {
        $user = User::factory()->create([
            'status' => 'suspended',
        ]);
        $ticket = Ticket::factory()->create();

        $this->actingAs($user);

        $this->patchJson("/api/tickets/{$ticket->id}", [
            'title' => '変更後',
        ])->assertForbidden();

        $this->deleteJson("/api/tickets/{$ticket->id}")
            ->assertForbidden();
    }

}
