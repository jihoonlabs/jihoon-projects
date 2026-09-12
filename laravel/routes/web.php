<?php

use App\Http\Controllers\AuthController;
use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});

Route::prefix('api/auth')->group(function () {
    // Google OAuth
    Route::get('google/redirect', [AuthController::class, 'googleRedirect']);
    Route::get('google/callback', [AuthController::class, 'googleCallback']);

    // LINE OAuth
    Route::get('line/redirect', [AuthController::class, 'lineRedirect']);
    Route::get('line/callback', [AuthController::class, 'lineCallback']);
});