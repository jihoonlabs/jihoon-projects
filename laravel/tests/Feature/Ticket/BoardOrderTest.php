<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\Feature\Ticket\Concerns\UsesGeneralProject;
use Tests\TestCase;

class BoardOrderTest extends TestCase
{
    use RefreshDatabase;
    use UsesGeneralProject;

    protected Project $project;

    protected function setUp(): void
    {
        parent::setUp();

        $user = User::factory()->create(['status' => 'active']);
        $this->actingAs($user);
        $this->project = $this->addToGeneralProject($user);
    }

    public function test_新規チケットは列の末尾に追加される(): void
    {
        Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'TODO',
            'position' => 0,
        ]);

        $response = $this->postJson('/api/tickets', [
            'project_id' => $this->project->id,
            'title' => '末尾チケット',
            'status' => 'TODO',
        ]);

        $response
            ->assertCreated()
            ->assertJsonPath('data.position', 1);

        $this->assertSame(1, $this->project->refresh()->board_version);
    }

    public function test_同一列内で並び替えできる(): void
    {
        $tickets = collect(range(0, 2))->map(fn (int $position) => Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'TODO',
            'position' => $position,
        ]));

        $response = $this->patchJson("/api/tickets/{$tickets[2]->id}/move", [
            'status' => 'TODO',
            'position' => 0,
            'board_version' => 0,
        ]);

        $response
            ->assertOk()
            ->assertJsonPath('data.position', 0)
            ->assertJsonPath('board_version', 1);

        $this->assertSame(
            [$tickets[2]->id, $tickets[0]->id, $tickets[1]->id],
            Ticket::query()->where('status', 'TODO')->orderBy('position')->pluck('id')->all()
        );
    }

    public function test_別列へ移動すると両方の列順が詰め直される(): void
    {
        $first = Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'TODO',
            'position' => 0,
        ]);
        $moving = Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'TODO',
            'position' => 1,
        ]);
        $target = Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'IN_PROGRESS',
            'position' => 0,
        ]);

        $this->patchJson("/api/tickets/{$moving->id}/move", [
            'status' => 'IN_PROGRESS',
            'position' => 0,
            'board_version' => 0,
        ])->assertOk();

        $this->assertDatabaseHas('tickets', [
            'id' => $first->id,
            'status' => 'TODO',
            'position' => 0,
        ]);
        $this->assertSame(
            [$moving->id, $target->id],
            Ticket::query()->where('status', 'IN_PROGRESS')->orderBy('position')->pluck('id')->all()
        );
    }

    public function test_古いboard_versionの移動は409で拒否される(): void
    {
        $ticket = Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'TODO',
            'position' => 0,
        ]);
        $this->project->forceFill(['board_version' => 2])->save();

        $this->patchJson("/api/tickets/{$ticket->id}/move", [
            'status' => 'IN_PROGRESS',
            'position' => 0,
            'board_version' => 1,
        ])->assertConflict();

        $this->assertDatabaseHas('tickets', [
            'id' => $ticket->id,
            'status' => 'TODO',
            'position' => 0,
        ]);
        $this->assertSame(2, $this->project->refresh()->board_version);
    }

    public function test_手動ステータス変更は移動先の末尾に追加される(): void
    {
        Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'IN_REVIEW',
            'position' => 0,
        ]);
        $ticket = Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'TODO',
            'position' => 0,
        ]);

        $this->patchJson("/api/tickets/{$ticket->id}", [
            'status' => 'IN_REVIEW',
        ])
            ->assertOk()
            ->assertJsonPath('data.position', 1);

        $this->assertSame(1, $this->project->refresh()->board_version);
    }
    public function test_削除すると列順が詰め直されboard_versionが更新される(): void
    {
        $first = Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'TODO',
            'position' => 0,
        ]);
        $deleted = Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'TODO',
            'position' => 1,
        ]);
        $last = Ticket::factory()->create([
            'project_id' => $this->project->id,
            'status' => 'TODO',
            'position' => 2,
        ]);

        $this->deleteJson("/api/tickets/{$deleted->id}")->assertOk();

        $this->assertDatabaseMissing('tickets', ['id' => $deleted->id]);
        $this->assertSame(
            [$first->id, $last->id],
            Ticket::query()
                ->where('project_id', $this->project->id)
                ->where('status', 'TODO')
                ->orderBy('position')
                ->pluck('id')
                ->all()
        );
        $this->assertDatabaseHas('tickets', [
            'id' => $last->id,
            'position' => 1,
        ]);
        $this->assertSame(1, $this->project->refresh()->board_version);
    }

}
