<?php

namespace Tests\Feature\Ticket;

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
}