<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\Feature\Ticket\Concerns\UsesGeneralProject;
use Tests\TestCase;

class StoreTest extends TestCase
{
    use RefreshDatabase;
    use UsesGeneralProject;

    protected Project $project;

    protected function setUp(): void
    {
        parent::setUp();

        $user = User::factory()->create([
            'status' => 'active',
        ]);

        $this->actingAs($user);
        $this->project = $this->addToGeneralProject($user);
    }

    public function test_チケットを作成できる(): void
    {
        $response = $this->postJson('/api/tickets', [
            'project_id' => $this->project->id,
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
            ->assertJsonPath('data.issue_key', $this->project->project_key.'-01');

        $this->assertDatabaseHas('tickets', [
            'id' => 1,
            'issue_key' => $this->project->project_key.'-01',
            'title' => 'テストチケット',
            'status' => 'TODO',
            'priority' => 'MEDIUM',
        ]);
    }

    public function test_ticket_numbers_increment_per_project(): void
    {
        $first = $this->postJson('/api/tickets', [
            'project_id' => $this->project->id,
            'title' => 'First',
        ])->assertCreated();

        $second = $this->postJson('/api/tickets', [
            'project_id' => $this->project->id,
            'title' => 'Second',
        ])->assertCreated();

        $otherProject = Project::factory()->create();
        $this->addProjectMember($otherProject, $this->project->members()->first(), permission: 'write');

        $other = $this->postJson('/api/tickets', [
            'project_id' => $otherProject->id,
            'title' => 'Other project',
        ])->assertCreated();

        $this->assertSame($this->project->project_key.'-01', $first->json('data.issue_key'));
        $this->assertSame($this->project->project_key.'-02', $second->json('data.issue_key'));
        $this->assertSame($otherProject->project_key.'-01', $other->json('data.issue_key'));
    }

    public function test_タイトルは必須(): void
    {
        $response = $this->postJson('/api/tickets', [
            'project_id' => $this->project->id,
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
            'project_id' => $this->project->id,
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
            'project_id' => $this->project->id,
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
