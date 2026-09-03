# Task Management System API (Laravel)

Next.js フロントエンドと連携するタスク・チケット管理システムのバックエンド API です。

--------------------------------------------------
Tech Stack
--------------------------------------------------
- Framework: Laravel 11+
- PHP: ^8.3
- Database: SQLite / MySQL
- Authentication: Laravel Sanctum (Bearer Token)

--------------------------------------------------
Environment Setup
--------------------------------------------------
git pull 後に実行する環境構築の手順です。

1. Install Dependencies
$ composer install
$ npm install

2. Environment Setup & Key Generation
$ copy .env.example .env
$ php artisan key:generate

3. Database Migration & API Setup
$ php artisan migrate
$ php artisan install:api

4. Run Server
$ php artisan serve

* API Base URL: http://127.0.0.1:8000

--------------------------------------------------
API Endpoints
--------------------------------------------------
[POST] /api/login
- Description: User Login & Issue Token
- Auth: Public

[POST] /api/logout
- Description: User Logout
- Auth: Required (Bearer Token)

[GET] /api/user
- Description: Get Current User Info
- Auth: Required (Bearer Token)

[GET] /api/tickets
- Description: Get Ticket List
- Auth: Required (Bearer Token)

[POST] /api/tickets
- Description: Create New Ticket
- Auth: Required (Bearer Token)