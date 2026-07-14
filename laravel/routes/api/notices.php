<?php

use App\Http\Controllers\NoticeController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Notice API Routes
|--------------------------------------------------------------------------
| routes/api.php에서 /notices 접두사를 붙인다.
|--------------------------------------------------------------------------
*/

// GET /api/notices
Route::get('/', [NoticeController::class, 'index']);

// GET /api/notices/{id}
Route::get('/{id}', [NoticeController::class, 'show']);

// POST /api/notices
Route::post('/', [NoticeController::class, 'store']);

// PUT /api/notices/{id}
Route::put('/{id}', [NoticeController::class, 'update']);

// DELETE /api/notices/{id}
Route::delete('/{id}', [NoticeController::class, 'destroy']);