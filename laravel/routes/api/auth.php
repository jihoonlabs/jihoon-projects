<?php

use App\Http\Controllers\AuthController;
use Illuminate\Support\Facades\Route;

// 認証不要
Route::post('login', [AuthController::class, 'login']);
Route::post('register', [AuthController::class, 'register']);

// 認証必須
Route::middleware('auth:sanctum')->group(function () {
    Route::get('me', [AuthController::class, 'user']);
    Route::post('logout', [AuthController::class, 'logout']);
});