# Laravel API

現在の `composer.lock` を再現するには **PHP 8.4以上とComposer 2** が必要です。`composer.json` のPHP制約は `^8.3` ですが、固定済みのSymfony 8系はPHP 8.4以上を要求します。CIはPHP 8.4・SQLiteで検証します。

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
```
