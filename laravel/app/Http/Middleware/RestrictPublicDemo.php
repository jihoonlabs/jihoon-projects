<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class RestrictPublicDemo
{
    public function handle(Request $request, Closure $next): Response
    {
        if (! config('demo.enabled')) {
            return $next($request);
        }

        // 共有デモアカウントによる公開コンテンツの変更を防ぐ。
        if (! $request->isMethodSafe() && $request->is('api/posts', 'api/posts/*', 'api/notices', 'api/notices/*')) {
            return response()->json(['message' => '公開デモでは投稿・お知らせを変更できません。'], 403);
        }

        // 公開デモでは外部アカウント・メールと接続しない。
        if ($request->is(
            'api/auth/register',
            'api/auth/forgot-password',
            'api/auth/reset-password',
            'api/auth/email/*',
            'api/auth/google/*',
            'api/auth/line/*',
        )) {
            return response()->json(['message' => '公開デモではこの操作を利用できません。体験用アカウントをご利用ください。'], 403);
        }

        return $next($request);
    }
}
