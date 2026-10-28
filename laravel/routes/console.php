<?php

use App\Models\User;
use Illuminate\Foundation\Inspiring;
use Illuminate\Support\Facades\Artisan;

Artisan::command('inspire', function () {
    $this->comment(Inspiring::quote());
})->purpose('Display an inspiring quote');

Artisan::command('attendance:set-role {user_id} {role}', function (string $userId, string $role) {
    if (in_array($role, ['employee', 'admin'], true) === false) {
        $this->error('Role must be either employee or admin.');

        return 1;
    }

    $user = User::query()->find($userId);
    if ($user === null) {
        $this->error('User not found.');

        return 1;
    }

    $user->attendance_role = $role;
    $user->save();

    $this->info("Attendance role for user {$user->id} set to {$role}.");

    return 0;
})->purpose('Assign an attendance role independently of the ticket role');
