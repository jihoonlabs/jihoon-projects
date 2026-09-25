<?php

use App\Http\Middleware\EnsureUserIsActive;
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        // Sanctum の SPA セッション認証を有効化
        $middleware->statefulApi();

        // APIパスのCSRFトークン検証例外処理
        $middleware->validateCsrfTokens(except: [
            'api/*',
        ]);

        // 停止中のユーザーによる認証必須 API へのアクセスを防止
        $middleware->alias([
            'active.user' => EnsureUserIsActive::class,
        ]);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        //
    })->create();
