# Laravel API

Next.jsフロントエンド用のLaravel APIです。

## 使用技術

- Laravel
- Laravel Sanctum
- Laravel Socialite
- SQLite / MySQL

## 主な機能

- メールアドレスによる会員登録・ログイン
- メールアドレス認証
- Google・LINEログイン
- パスワード再設定

## セットアップ

```bash
composer install
cp .env.example .env
php artisan key:generate
php artisan migrate
php artisan serve

php artisan test