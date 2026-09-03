<?php

use App\Http\Controllers\AuthController;
use Illuminate\Support\Facades\Route;

// /api/auth/login
Route::post('login', [AuthController::class, 'login']);

// Sanctum Bearer Token
Route::middleware('auth:sanctum')->group(function () {
    Route::get('me', [AuthController::class, 'user']);      // /api/auth/me
    Route::post('logout', [AuthController::class, 'logout']); // /api/auth/logout
});