<?php

use App\Http\Controllers\AuthController;
use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});

Route::prefix('api/auth')->group(function () {
    Route::get('{provider}/redirect', [AuthController::class, 'socialRedirect']);
    Route::get('{provider}/callback', [AuthController::class, 'socialCallback']);
});