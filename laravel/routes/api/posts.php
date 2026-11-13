<?php

use App\Http\Controllers\PostController;
use App\Http\Middleware\RestrictPublicDemo;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Post API Routes
|--------------------------------------------------------------------------
| 이 파일의 경로에는 routes/api.php에서 /posts 접두사를 붙인다.
|--------------------------------------------------------------------------
*/

// GET /api/posts
Route::get('/', [PostController::class, 'index']);
Route::get('/{post}', [PostController::class, 'show']);

Route::middleware(['auth:sanctum', 'active.user', RestrictPublicDemo::class])->group(function () {
    Route::post('/', [PostController::class, 'store']);
    Route::put('/{post}', [PostController::class, 'update']);
    Route::delete('/{post}', [PostController::class, 'destroy']);
});
