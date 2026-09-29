<?php

namespace Tests\Feature\Attendance;

use App\Models\AttendanceRecord;
use App\Models\User;
use Carbon\CarbonImmutable;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class AttendanceApiTest extends TestCase
{
    use RefreshDatabase;

    protected function tearDown(): void
    {
        CarbonImmutable::setTestNow();
        parent::tearDown();
    }

    public function test_user_can_clock_in_once_and_clock_out_once(): void
    {
        CarbonImmutable::setTestNow('2026-09-29T00:00:00Z');
        $user = User::factory()->create();
        $this->actingAs($user);

        $this->getJson('/api/attendance/today')
            ->assertOk()
            ->assertJsonPath('data.status', 'not_started')
            ->assertJsonPath('data.record', null);

        $this->postJson('/api/attendance/clock-out')
            ->assertStatus(409)
            ->assertJsonPath('code', 'not_working');

        $this->postJson('/api/attendance/clock-in')
            ->assertCreated()
            ->assertJsonPath('data.work_date', '2026-09-29')
            ->assertJsonPath('data.clock_in_at', '2026-09-29T00:00:00+00:00')
            ->assertJsonPath('data.clock_out_at', null);

        $this->getJson('/api/attendance/today')
            ->assertJsonPath('data.status', 'working');

        $this->postJson('/api/attendance/clock-in')
            ->assertStatus(409)
            ->assertJsonPath('code', 'already_clocked_in');

        CarbonImmutable::setTestNow('2026-09-29T01:31:00Z');
        $this->postJson('/api/attendance/clock-out')
            ->assertOk()
            ->assertJsonPath('data.duration_minutes', 91)
            ->assertJsonPath('data.clock_out_at', '2026-09-29T01:31:00+00:00');

        $this->getJson('/api/attendance/today')
            ->assertJsonPath('data.status', 'finished');

        $this->postJson('/api/attendance/clock-out')
            ->assertStatus(409)
            ->assertJsonPath('code', 'not_working');
        $this->postJson('/api/attendance/clock-in')
            ->assertStatus(409);

        $this->assertDatabaseCount('attendance_records', 1);
    }

    public function test_overnight_clock_out_belongs_to_clock_in_date(): void
    {
        $user = User::factory()->create();
        $this->actingAs($user);
        CarbonImmutable::setTestNow('2026-09-29T14:59:00Z');
        $this->postJson('/api/attendance/clock-in')
            ->assertJsonPath('data.work_date', '2026-09-29');

        CarbonImmutable::setTestNow('2026-09-29T15:30:00Z');
        $this->getJson('/api/attendance/today')
            ->assertJsonPath('data.date', '2026-09-30')
            ->assertJsonPath('data.status', 'working')
            ->assertJsonPath('data.record.work_date', '2026-09-29');

        $this->postJson('/api/attendance/clock-in')
            ->assertStatus(409);
        $this->postJson('/api/attendance/clock-out')
            ->assertOk()
            ->assertJsonPath('data.work_date', '2026-09-29')
            ->assertJsonPath('data.duration_minutes', 31);

        $this->getJson('/api/attendance/today')
            ->assertJsonPath('data.status', 'not_started');
        $this->postJson('/api/attendance/clock-in')
            ->assertCreated()
            ->assertJsonPath('data.work_date', '2026-09-30');
    }

    public function test_list_and_actions_are_scoped_to_authenticated_user(): void
    {
        $first = User::factory()->create();
        $second = User::factory()->create();
        AttendanceRecord::create([
            'user_id' => $second->id,
            'work_date' => '2026-09-27',
            'clock_in_at' => '2026-09-27T00:00:00Z',
            'clock_out_at' => '2026-09-27T08:00:00Z',
        ]);
        CarbonImmutable::setTestNow('2026-09-29T00:00:00Z');
        $this->actingAs($first);

        $this->getJson('/api/attendance')->assertOk()->assertJsonCount(0, 'data');
        $this->postJson('/api/attendance/clock-in', ['user_id' => $second->id])
            ->assertCreated();
        $this->assertDatabaseHas('attendance_records', [
            'user_id' => $first->id,
            'work_date' => '2026-09-29',
        ]);
        $this->getJson('/api/attendance')
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.work_date', '2026-09-29');
    }

    public function test_guest_and_suspended_user_cannot_access_attendance(): void
    {
        $this->getJson('/api/attendance/today')->assertUnauthorized();
        $this->postJson('/api/attendance/clock-in')->assertUnauthorized();

        $this->actingAs(User::factory()->create(['status' => 'suspended']));
        $this->getJson('/api/attendance')->assertForbidden();
    }
}
