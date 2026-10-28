<?php

namespace Tests\\Feature\\Attendance;

use App\\Models\\User;
use Illuminate\\Foundation\\Testing\\RefreshDatabase;
use Tests\\TestCase;

class AttendanceRoleCommandTest extends TestCase
{
    use RefreshDatabase;

    public function test_attendance_role_can_be_assigned_without_changing_ticket_role(): void
    {
        $user = User::factory()->create(['role' => 'user']);

        $this->artisan('attendance:set-role', [
            'user_id' => (string) $user->id,
            'role' => 'admin',
        ])
            ->expectsOutput("Attendance role for user {$user->id} set to admin.")
            ->assertExitCode(0);

        $this->assertDatabaseHas('users', [
            'id' => $user->id,
            'role' => 'user',
            'attendance_role' => 'admin',
        ]);
    }

    public function test_attendance_role_command_rejects_unknown_roles_and_users(): void
    {
        $user = User::factory()->create();

        $this->artisan('attendance:set-role', [
            'user_id' => (string) $user->id,
            'role' => 'ticket-admin',
        ])
            ->expectsOutput('Role must be either employee or admin.')
            ->assertExitCode(1);

        $this->artisan('attendance:set-role', [
            'user_id' => '999999',
            'role' => 'admin',
        ])
            ->expectsOutput('User not found.')
            ->assertExitCode(1);

        $this->assertDatabaseHas('users', [
            'id' => $user->id,
            'attendance_role' => 'employee',
        ]);
    }
}
