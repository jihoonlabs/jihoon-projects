<?php

use App\Http\Controllers\Auth\EmailVerificationNotificationController;
use App\Http\Controllers\AuthController;
use Illuminate\Support\Facades\Route;

// 認証不要
Route::post(
    'email/verification-notification',
    EmailVerificationNotificationController::class,
)
    ->middleware('throttle:6,1')
    ->name('verification.send');

Route::post('login', [AuthController::class, 'login'])
    ->middleware('throttle:5,1');
Route::post('register', [AuthController::class, 'register'])
    ->middleware('throttle:3,1');

// 認証必須
Route::middleware([
    'auth:sanctum',
    'active.user',
])->group(function () {
    Route::get('me', [AuthController::class, 'user']);
    Route::post('logout', [AuthController::class, 'logout']);
});
