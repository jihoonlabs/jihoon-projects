<?php

use App\Http\Controllers\Attendance\AttendanceController;
use Illuminate\Support\Facades\Route;

Route::middleware(['auth:sanctum', 'active.user'])->group(function () {
    Route::get('/today', [AttendanceController::class, 'today']);
    Route::get('/', [AttendanceController::class, 'index']);
    Route::post('/clock-in', [AttendanceController::class, 'clockIn']);
    Route::post('/clock-out', [AttendanceController::class, 'clockOut']);
});
