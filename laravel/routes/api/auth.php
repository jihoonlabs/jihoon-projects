<?php

use App\Http\Controllers\AuthController;
use Illuminate\Support\Facades\Route;

// 공개 라우트 (/api/auth/*)
Route::post('login', [AuthController::class, 'login']);
Route::post('register', [AuthController::class, 'register']);

// Sanctum Bearer Token
Route::middleware('auth:sanctum')->group(function () {
    Route::get('me', [AuthController::class, 'user']);      // /api/auth/me
    Route::post('logout', [AuthController::class, 'logout']); // /api/auth/logout
});