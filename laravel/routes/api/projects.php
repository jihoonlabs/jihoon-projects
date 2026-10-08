<?php

use App\Http\Controllers\Projects\ProjectController;
use App\Http\Controllers\Projects\ProjectMemberController;
use Illuminate\Support\Facades\Route;

Route::middleware([
    'auth:sanctum',
    'active.user',
])->group(function () {
    Route::get('/', [ProjectController::class, 'index']);
    Route::post('/', [ProjectController::class, 'store']);
    Route::get('/{project}', [ProjectController::class, 'show']);
    Route::patch('/{project}', [ProjectController::class, 'update']);
    Route::delete('/{project}', [ProjectController::class, 'destroy']);
    Route::post('/{project}/archive', [ProjectController::class, 'archive']);
    Route::post('/{project}/restore', [ProjectController::class, 'restore']);

    Route::get('/{project}/members', [ProjectMemberController::class, 'index']);
    Route::post('/{project}/members', [ProjectMemberController::class, 'store']);
    Route::patch('/{project}/members/{user}', [ProjectMemberController::class, 'update']);
    Route::delete('/{project}/members/{user}', [ProjectMemberController::class, 'destroy']);
});
