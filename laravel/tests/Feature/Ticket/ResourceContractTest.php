<?php

namespace Tests\Feature\Ticket;

use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ResourceContractTest extends TestCase
{
    use RefreshDatabase;

    public function test_all_ticket_endpoints_return_the_same_snake_case_contract(): void
    {
        $user = User::factory()->create(['status' => 'active']);
        $this->actingAs($user);
        $ticket = Ticket::factory()->create(['assignee_id' => $user->id]);

        $responses = [
            [$this->getJson('/api/tickets')->assertOk(), 'data.0'],
            [$this->getJson('/api/tickets/'.$ticket->id)->assertOk(), 'data'],
            [$this->patchJson('/api/tickets/'.$ticket->id, ['status' => 'DONE'])->assertOk(), 'data'],
            [$this->postJson('/api/tickets', ['title' => 'Assigned', 'assignee_id' => $user->id])->assertCreated(), 'data'],
        ];

        foreach ($responses as [$response, $path]) {
            $data = $response->json($path);
            $this->assertEqualsCanonicalizing([
                'id', 'issue_key', 'title', 'description', 'status', 'priority',
                'assignee', 'created_at', 'updated_at',
            ], array_keys($data));
            $this->assertIsString($data['id']);
            $this->assertNotNull($data['created_at']);
            $this->assertNotNull($data['updated_at']);
            $this->assertSame($user->id, $data['assignee']['id']);
            $this->assertSame($user->name, $data['assignee']['name']);
            $this->assertEqualsCanonicalizing(['id', 'name', 'avatar_url'], array_keys($data['assignee']));
            $this->assertNull($data['assignee']['avatar_url']);
        }
    }

    public function test_nullable_values_remain_null(): void
    {
        $this->actingAs(User::factory()->create(['status' => 'active']));
        $ticket = Ticket::factory()->create(['issue_key' => null, 'description' => null, 'assignee_id' => null]);
        $this->getJson('/api/tickets/'.$ticket->id)
            ->assertOk()
            ->assertJsonPath('data.issue_key', null)
            ->assertJsonPath('data.description', null)
            ->assertJsonPath('data.assignee', null);
    }
}
