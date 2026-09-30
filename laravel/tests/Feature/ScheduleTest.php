<?php

namespace Tests\Feature;

use App\Models\Schedule;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Tests\TestCase;

class ScheduleTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_create_and_list_only_their_schedules(): void
    {
        $user = User::factory()->create();
        $other = User::factory()->create();

        Schedule::query()->create([
            'user_id' => $other->id,
            'title' => 'Other schedule',
            'starts_at' => '2026-09-30 01:00:00',
            'ends_at' => '2026-09-30 02:00:00',
        ]);

        Sanctum::actingAs($user);

        $this->postJson('/api/schedules', [
            'title' => 'Meeting',
            'starts_at' => '2026-09-30T03:00:00Z',
            'ends_at' => '2026-09-30T04:00:00Z',
            'memo' => 'Calendar MVP',
        ])->assertCreated()
            ->assertJsonPath('data.title', 'Meeting');

        $this->getJson('/api/schedules?from=2026-09-01T00:00:00Z&to=2026-10-01T00:00:00Z')
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.title', 'Meeting');
    }

    public function test_user_can_update_and_delete_their_schedule(): void
    {
        $user = User::factory()->create();
        $schedule = Schedule::query()->create([
            'user_id' => $user->id,
            'title' => 'Before',
            'starts_at' => '2026-09-30 03:00:00',
            'ends_at' => '2026-09-30 04:00:00',
        ]);

        Sanctum::actingAs($user);

        $this->putJson("/api/schedules/{$schedule->id}", [
            'title' => 'After',
            'starts_at' => '2026-09-30T03:00:00Z',
            'ends_at' => '2026-09-30T05:00:00Z',
            'memo' => null,
        ])->assertOk()
            ->assertJsonPath('data.title', 'After');

        $this->deleteJson("/api/schedules/{$schedule->id}")
            ->assertNoContent();

        $this->assertDatabaseMissing('schedules', ['id' => $schedule->id]);
    }

    public function test_user_cannot_update_or_delete_another_users_schedule(): void
    {
        $owner = User::factory()->create();
        $other = User::factory()->create();
        $schedule = Schedule::query()->create([
            'user_id' => $owner->id,
            'title' => 'Private',
            'starts_at' => '2026-09-30 03:00:00',
            'ends_at' => '2026-09-30 04:00:00',
        ]);

        Sanctum::actingAs($other);

        $payload = [
            'title' => 'Changed',
            'starts_at' => '2026-09-30T03:00:00Z',
            'ends_at' => '2026-09-30T05:00:00Z',
        ];

        $this->putJson("/api/schedules/{$schedule->id}", $payload)->assertNotFound();
        $this->deleteJson("/api/schedules/{$schedule->id}")->assertNotFound();
    }

    public function test_schedule_requires_valid_time_range(): void
    {
        Sanctum::actingAs(User::factory()->create());

        $this->postJson('/api/schedules', [
            'title' => 'Invalid',
            'starts_at' => '2026-09-30T04:00:00Z',
            'ends_at' => '2026-09-30T03:00:00Z',
        ])->assertUnprocessable()
            ->assertJsonValidationErrors('ends_at');
    }

    public function test_guest_cannot_access_schedules(): void
    {
        $this->getJson('/api/schedules?from=2026-09-01&to=2026-10-01')
            ->assertUnauthorized();
    }
}
