<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class RestrictPublicDemo
{
    public function handle(Request $request, Closure $next): Response
    {
        // 公開デモでは外部アカウント・メールと接続しない。
        if (config('demo.enabled') && $request->is(
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
