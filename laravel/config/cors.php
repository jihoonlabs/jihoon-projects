<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Cross-Origin Resource Sharing (CORS) Configuration
    |--------------------------------------------------------------------------
    |
    | Next.js から Laravel API へのクロスオリジン通信を許可します。
    | Sanctum の SPA 認証で Cookie を送受信するため、
    | credentials を有効にします。
    |
    */

    'paths' => ['api/*', 'sanctum/csrf-cookie'],

    'allowed_methods' => ['*'],

    // Next.js の開発環境のみ許可
    'allowed_origins' => [
        env('FRONTEND_URL', 'http://localhost:3000'),
    ],

    'allowed_origins_patterns' => [],

    'allowed_headers' => ['*'],

    'exposed_headers' => [],

    'max_age' => 0,

    // Sanctum SPA 認証で Cookie を送受信するために必要
    'supports_credentials' => true,

];