<?php

namespace Tests\Feature\Ticket;

use App\Models\Ticket;
use App\Models\User;
use Illuminate\Database\Events\TransactionCommitted;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Event;
use Tests\Feature\Ticket\Concerns\UsesGeneralProject;
use Tests\TestCase;

class EditConcurrencyTest extends TestCase
{
    use RefreshDatabase;
    use UsesGeneralProject;

    private function writer(): User
    {
        $user = User::factory()->create(['status' => 'active']);
        $this->addToGeneralProject($user);

        return $user;
    }

    public function test_two_editors_of_the_same_version_cannot_overwrite_each_other_even_in_the_same_second(): void
    {
        $this->freezeTime();
        $first = $this->writer();
        $second = $this->writer();
        $ticket = Ticket::factory()->create(['status' => 'TODO']);
        $path = '/api/tickets/'.$ticket->id;
        $version = $this->actingAs($first)->getJson($path)->assertOk()->json('data.version');
        $this->actingAs($second)->getJson($path)->assertJsonPath('data.version', $version);
        $timestamp = $ticket->updated_at;
        $boardVersion = $ticket->project->board_version;

        $this->actingAs($first)->patchJson($path, ['title' => 'First writer', 'expected_version' => $version])
            ->assertOk()->assertJsonPath('data.version', $version + 1);
        $this->actingAs($second)->patchJson($path, ['title' => 'Stale writer', 'status' => 'DONE', 'expected_version' => $version])
            ->assertConflict()->assertJsonPath('code', 'ticket_conflict');
        $ticket->refresh();
        $this->assertSame('First writer', $ticket->title);
        $this->assertSame('TODO', $ticket->status);
        $this->assertTrue($timestamp->equalTo($ticket->updated_at));
        $this->assertSame($boardVersion, $ticket->project()->first()->board_version);
    }

    public function test_version_condition_is_part_of_the_atomic_update_sql(): void
    {
        $this->actingAs($this->writer());
        $ticket = Ticket::factory()->create();
        $grammar = DB::connection()->getQueryGrammar();
        $table = $grammar->wrapTable('tickets');
        $versionColumn = $grammar->wrap('version');
        $updates = [];
        DB::listen(function ($query) use (&$updates, $table) {
            if (str_starts_with(strtolower($query->sql), 'update '.$table)) {
                $updates[] = $query;
            }
        });
        $this->patchJson('/api/tickets/'.$ticket->id, ['title' => 'Atomic', 'expected_version' => 1])->assertOk();
        $this->assertCount(1, $updates);
        $this->assertStringContainsString($versionColumn.' = version + 1', $updates[0]->sql);
        $this->assertStringContainsString('and '.$versionColumn.' = ?', $updates[0]->sql);
        $this->assertSame(1, end($updates[0]->bindings));
    }

    public function test_legacy_field_and_status_writes_advance_the_ticket_version(): void
    {
        $this->actingAs($this->writer());
        $ticket = Ticket::factory()->create(['status' => 'TODO']);
        $path = '/api/tickets/'.$ticket->id;
        $this->patchJson($path, ['title' => 'Legacy'])->assertOk()->assertJsonPath('data.version', 2);
        $this->patchJson($path, ['status' => 'DONE'])->assertOk()->assertJsonPath('data.version', 3);
        $this->patchJson($path, ['description' => 'Stale', 'expected_version' => 1])->assertConflict();
        $this->assertSame('Legacy', $ticket->refresh()->title);
        $this->assertSame('DONE', $ticket->status);
    }

    public function test_move_and_shifted_positions_invalidate_stale_edit_versions(): void
    {
        $this->actingAs($user = $this->writer());
        $project = $this->addToGeneralProject($user);
        $first = Ticket::factory()->create(['status' => 'TODO', 'position' => 0]);
        $second = Ticket::factory()->create(['status' => 'TODO', 'position' => 1]);
        $this->patchJson('/api/tickets/'.$second->id.'/move', [
            'status' => 'TODO', 'position' => 0, 'board_version' => $project->board_version,
        ])->assertOk();
        foreach ([$first, $second] as $ticket) {
            $this->assertGreaterThan(1, $ticket->refresh()->version);
            $this->patchJson('/api/tickets/'.$ticket->id, ['title' => 'Stale', 'expected_version' => 1])->assertConflict();
        }
        $this->assertSame(1, $first->position);
        $this->assertSame(0, $second->position);
    }

    public function test_refetch_allows_explicit_new_edit_and_assignee_changes_persist(): void
    {
        $this->actingAs($this->writer());
        $other = $this->writer();
        $ticket = Ticket::factory()->create();
        $path = '/api/tickets/'.$ticket->id;
        $this->patchJson($path, ['assignee_id' => $other->id, 'expected_version' => 1])->assertOk();
        $latest = $this->getJson($path)->assertOk()->json('data');
        $this->patchJson($path, ['title' => 'New edit', 'expected_version' => $latest['version']])
            ->assertOk()->assertJsonPath('data.assignee.id', $other->id)->assertJsonPath('data.version', 3);
    }

    public function test_deleted_and_inaccessible_tickets_are_distinct_from_version_conflicts(): void
    {
        $this->actingAs($writer = $this->writer());
        $ticket = Ticket::factory()->create();
        $project = $ticket->project;
        $project->members()->detach($writer->id);
        $this->getJson('/api/tickets/'.$ticket->id)->assertForbidden();
        $this->patchJson('/api/tickets/'.$ticket->id, ['title' => 'Denied', 'expected_version' => 1])->assertForbidden();
        $ticket->delete();
        $this->getJson('/api/tickets/'.$ticket->id)->assertNotFound();
        $this->patchJson('/api/tickets/'.$ticket->id, ['title' => 'Deleted', 'expected_version' => 1])->assertNotFound();
    }

    public function test_save_response_keeps_the_locked_snapshot_when_a_later_write_arrives_before_serialization(): void
    {
        $this->actingAs($this->writer());
        $ticket = Ticket::factory()->create();
        $interleaved = false;
        // 同一接続でtransaction終了イベントと応答生成の間を再現する。物理commitの検証ではない。
        Event::listen(TransactionCommitted::class, function () use ($ticket, &$interleaved) {
            if ($interleaved) {
                return;
            }
            $interleaved = true;
            DB::table('tickets')->where('id', $ticket->id)
                ->update(['title' => 'Later writer', 'version' => DB::raw('version + 1')]);
        });
        $path = '/api/tickets/'.$ticket->id;
        $this->patchJson($path, ['title' => 'My saved snapshot', 'expected_version' => 1])
            ->assertOk()->assertJsonPath('data.title', 'My saved snapshot')->assertJsonPath('data.version', 2);
        $this->assertTrue($interleaved);
        $this->assertSame('Later writer', $ticket->refresh()->title);
        $this->assertSame(3, $ticket->version);
        $this->patchJson($path, ['title' => 'Stale next edit', 'expected_version' => 2])->assertConflict();
    }

    public function test_invalid_conditional_versions_are_rejected(): void
    {
        $this->actingAs($this->writer());
        $ticket = Ticket::factory()->create();
        foreach ([null, 0, -1, 'bad', 1.5] as $version) {
            $this->patchJson('/api/tickets/'.$ticket->id, ['title' => 'Invalid', 'expected_version' => $version])
                ->assertUnprocessable()->assertJsonValidationErrors('expected_version');
        }
        $this->assertSame(1, $ticket->refresh()->version);
    }
}
