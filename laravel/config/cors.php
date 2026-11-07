<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Cross-Origin Resource Sharing (CORS) Configuration
    |--------------------------------------------------------------------------
    |
    | Next.js・Vue から Laravel API へのクロスオリジン通信を許可します。
    | Sanctum の SPA 認証で Cookie を送受信するため、
    | credentials を有効にします。
    |
    */

    'paths' => ['api/*', 'sanctum/csrf-cookie'],

    'allowed_methods' => ['*'],

    // services.frontend.clients と同じフロントエンドのみ許可（未設定のURLは除外）
    'allowed_origins' => array_values(array_filter([
        env('FRONTEND_URL', 'http://localhost:3000'),
        env('FRONTEND_VUE_URL'),
    ])),

    'allowed_origins_patterns' => [],

    'allowed_headers' => ['*'],

    'exposed_headers' => [],

    'max_age' => 0,

    // Sanctum SPA 認証で Cookie を送受信するために必要
    'supports_credentials' => true,

];
