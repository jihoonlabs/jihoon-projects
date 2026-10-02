<?php

use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
| ドメイン別の API ルーティングファイルをここで登録
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

// /api/auth/*
Route::prefix('auth')->group(
    base_path('routes/api/auth.php')
);

// /api/tickets/*
Route::prefix('tickets')->group(
    base_path('routes/api/tickets.php')
);
