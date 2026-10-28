<?php

use App\Http\Controllers\Attendance\AttendanceController;
use App\Http\Controllers\Attendance\AttendanceScheduleController;
use Illuminate\Support\Facades\Route;

Route::middleware(['auth:sanctum', 'active.user'])->group(function () {
    Route::get('/today', [AttendanceController::class, 'today']);
    Route::get('/', [AttendanceController::class, 'index']);
    Route::get('/schedule-users', [AttendanceScheduleController::class, 'users']);
    Route::get('/schedule', [AttendanceScheduleController::class, 'show']);
    Route::put('/schedule', [AttendanceScheduleController::class, 'store']);
    Route::post('/clock-in', [AttendanceController::class, 'clockIn']);
    Route::post('/clock-out', [AttendanceController::class, 'clockOut']);
    Route::post('/break-start', [AttendanceController::class, 'startBreak']);
    Route::post('/break-end', [AttendanceController::class, 'endBreak']);
});
