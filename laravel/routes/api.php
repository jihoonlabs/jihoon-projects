<?php

use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
| 도메인별 API Route 파일을 이곳에서 등록한다.
|--------------------------------------------------------------------------
*/

// /api/notices/*
Route::prefix('notices')->group(
    base_path('routes/api/notices.php')
);

// /api/posts/*
Route::prefix('posts')->group(
    base_path('routes/api/posts.php')
);