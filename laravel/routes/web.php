<?php

use App\Http\Controllers\Auth\EmailVerificationController;
use App\Http\Controllers\AuthController;
use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});

Route::prefix('api/auth')->group(function () {
    Route::get(
        'email/verify/{id}/{hash}',
        EmailVerificationController::class,
    )
        ->middleware(['signed', 'throttle:6,1'])
        ->name('verification.verify');

    Route::get('{provider}/redirect', [AuthController::class, 'socialRedirect']);
    Route::get('{provider}/callback', [AuthController::class, 'socialCallback']);
});
