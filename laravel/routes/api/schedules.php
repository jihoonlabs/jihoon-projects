<?php

use App\Http\Controllers\ScheduleController;
use Illuminate\Support\Facades\Route;

Route::middleware([
    'auth:sanctum',
    'active.user',
])->group(function () {
    Route::get('/', [ScheduleController::class, 'index']);
    Route::post('/', [ScheduleController::class, 'store']);
    Route::put('{schedule}', [ScheduleController::class, 'update']);
    Route::delete('{schedule}', [ScheduleController::class, 'destroy']);
});
