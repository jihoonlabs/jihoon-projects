# Task Management System API

Next.js フロントエンドと連携する、タスク・チケット管理システムの Laravel API です。

## Tech Stack

- Laravel
- PHP
- Laravel Sanctum
- Laravel Socialite
- Google OAuth
- SQLite / MySQL

## Authentication

- Email / Password Login
- Session-based Authentication
- CSRF Protection
- Google OAuth Login
- Verified Email による既存アカウント連携
- Social Account Management
- Laravel Feature Tests

## Setup

```bash
composer install
cp .env.example .env
php artisan key:generate
php artisan migrate
php artisan serve
```

Google OAuth を利用する場合は `.env` に認証情報を設定してください。

```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
FRONTEND_URL=http://localhost:3000
```

## Test

```bash
php artisan test
```