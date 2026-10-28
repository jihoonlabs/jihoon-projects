<?php

use Illuminate\Foundation\Inspiring;
use App\Models\User;
use Illuminate\Support\Facades\Artisan;

Artisan::command('inspire', function () {
    $this->comment(Inspiring::quote());
})->purpose('Display an inspiring quote');


Artisan::command('attendance:set-role {user_id} {role}', function (string $userId, string $role) {
    if (! in_array($role, ['employee', 'admin'], true)) {
        $this->error('Role must be either employee or admin.');

        return self::INVALID;
    }

    $user = User::query()->find($userId);
    if ($user === null) {
        $this->error('User not found.');

        return self::FAILURE;
    }

    $user->attendance_role = $role;
    $user->save();

    $this->info("Attendance role for user {$user->id} set to {$role}.");

    return self::SUCCESS;
})->purpose('Assign an attendance role independently of the ticket role');
