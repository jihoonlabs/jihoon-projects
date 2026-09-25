<?php

namespace Tests\Feature\Ticket;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class StoreTest extends TestCase
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

    public function test_チケットを作成できる(): void
    {
        $response = $this->postJson('/api/tickets', [
            'title' => 'テストチケット',
            'description' => 'テスト用の説明',
            'status' => 'TODO',
            'priority' => 'MEDIUM',
            'assignee_id' => null,
        ]);

        $response
            ->assertCreated()
            ->assertJsonPath('data.title', 'テストチケット')
            ->assertJsonPath('data.status', 'TODO')
            ->assertJsonPath('data.priority', 'MEDIUM')
            ->assertJsonPath('data.issueKey', 'TICK-1');

        $this->assertDatabaseHas('tickets', [
            'id' => 1,
            'issue_key' => 'TICK-1',
            'title' => 'テストチケット',
            'status' => 'TODO',
            'priority' => 'MEDIUM',
        ]);
    }

    public function test_タイトルは必須(): void
    {
        $response = $this->postJson('/api/tickets', [
            'description' => 'テスト用の説明',
            'status' => 'TODO',
            'priority' => 'MEDIUM',
            'assignee_id' => null,
        ]);

        $response
            ->assertUnprocessable()
            ->assertJsonValidationErrors(['title']);

        $this->assertDatabaseCount('tickets', 0);
    }

    public function test_不正な優先度は指定できない(): void
    {
        $response = $this->postJson('/api/tickets', [
            'title' => 'テストチケット',
            'description' => 'テスト用の説明',
            'status' => 'TODO',
            'priority' => 'URGENT',
            'assignee_id' => null,
        ]);

        $response
            ->assertUnprocessable()
            ->assertJsonValidationErrors(['priority']);

        $this->assertDatabaseCount('tickets', 0);
    }

    public function test_ステータスと優先度を省略した場合はデフォルト値で作成される(): void
    {
        $response = $this->postJson('/api/tickets', [
            'title' => 'テストチケット',
        ]);

        $response
            ->assertCreated()
            ->assertJsonPath('data.status', 'TODO')
            ->assertJsonPath('data.priority', 'MEDIUM');

        $this->assertDatabaseHas('tickets', [
            'title' => 'テストチケット',
            'status' => 'TODO',
            'priority' => 'MEDIUM',
        ]);
    }
}
