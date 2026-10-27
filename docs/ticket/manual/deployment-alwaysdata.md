# 公開デモの配置手順（alwaysdata）

この手順は公開V1の体験環境用です。React / Next.jsを静的出力し、Laravelと同じHTTPS originに配置します。通常の開発用Next.jsサーバーも引き続き使用できます。

## 公開する範囲

- ログイン画面に表示する `demo@example.com` / `TicketDemo2026!` は公開専用の体験資格情報です。管理者ではありません。
- 架空プロジェクトと5枚のチケットを用意します。共有アカウントでボード操作、チケット編集、コメントを試せます。
- 出退勤も体験できます。打刻やチケットの変更は閲覧者間で共有されます。実データ・個人情報・既存の利用者DBは持ち込まないでください。
- `TICKET_DEMO_MODE=true` の場合、新規登録、メール送信、パスワード再設定、Google/LINE認証をAPI側で拒否します。通常環境では無効です。
- `DemoSeeder` はデモモードかつ利用者・チケットが存在しないDBだけで実行できます。既存の `DatabaseSeeder` / `TicketSeeder` は実行しません。

## 1. アカウント側の準備

1. alwaysdataのSmallを選択します。公開ポートフォリオ用のためFree枠は使いません。Smallはディスク50GB・RAM 1GBで、月払い€6/月（税別）、年払いは月額換算€5（税別）です。2026-10-26の参考レートでは、月払いは約1,060円/月（税・カード手数料別）です。申込画面に表示される請求額を確認してください。
2. PHPは **8.4** を選択します。composer.jsonのPHP下限は8.3ですが、現在のlockfileはSymfony 8を含むため8.4が必要です。CLIとWebの両方で確認します。
3. デモ専用MariaDBと、そのDBだけに権限を持つ利用者を作成します。DB名例は `ACCOUNT_ticket_demo`。実際のホスト名・DB名・ユーザー名は管理画面の値を使用します。
4. SSH接続情報を確認します。秘密情報はGitHubやREADMEに貼らず、サーバー上の `.env` のみに設定します。

## 2. 手元で配布物を作る

対象の作業ブランチを取得してから、リポジトリのルートで実行します。Node.js 22以上、pnpm、Git、tarが必要です。依存関係はlockfileを更新しません。

```bash
git fetch origin deploy/ticket-alwaysdata-demo
git switch deploy/ticket-alwaysdata-demo
pnpm --dir react install --frozen-lockfile
node deploy/alwaysdata/build.mjs
```

最後に表示される `ticket-demo.tar.gz` が配布物です。`.env`、DB、ログ、node_modules、非公開資料は含みません。PHP vendorはサーバーでlockfileから導入します。ブランチのコミット済みファイルを配布対象として使うため、新しい変更はcommit後にビルドします。

`NEXT_PUBLIC_API_URL` を空文字にしたビルドで、APIは相対URLになります。ビルド時に `NEXT_PUBLIC_DEMO_MODE=true` を設定します。これは公開設定であり秘密情報ではありません。

## 3. 新しい配置先に展開

SSHまたはSFTPで配布物をホームディレクトリ配下へ転送します。初回は空の専用ディレクトリを作成してそこで展開します。既存環境へ上書きしないでください。

```bash
mkdir ticket-demo-release
cd ticket-demo-release
# このディレクトリへticket-demo.tar.gzを転送してから実行
tar -xzf ticket-demo.tar.gz
cd ticket-demo
php -v
composer install --no-dev --prefer-dist --optimize-autoloader --no-interaction
composer check-platform-reqs --no-dev
cp .env.example .env
chmod 600 .env
```

サーバーで `.env` を編集します。`ACCOUNT`、DBホスト・ユーザー・パスワードを置換し、以下を確認します。

- `APP_URL` / `FRONTEND_URL`: 同じ `https://ACCOUNT.alwaysdata.net`。末尾の `/` は不要。
- `SANCTUM_STATEFUL_DOMAINS`: スキームなしの `ACCOUNT.alwaysdata.net`。
- `SESSION_DOMAIN=null`、`SESSION_SECURE_COOKIE=true`、`APP_DEBUG=false`。
- `DB_CONNECTION=mysql`、専用DB接続、`TICKET_DEMO_MODE=true`。
- OAuthの秘密値や個人メールの資格情報は設定不要。

```bash
php artisan key:generate --force
php artisan migrate --force
php artisan db:seed --class=DemoSeeder --force
php artisan config:cache
php artisan route:cache
php artisan view:cache
du -sh .
```

`APP_KEY` は初回だけ生成します。既存リリースの更新で再生成しないでください。`storage/` と `bootstrap/cache/` はPHPから書き込み可能にし、公開ルートには置きません。容量はログ・DBも含めてSmallのディスク枠内か管理画面で確認します。

## 4. Web設定

- Web > Sitesで種類 **PHP**、PHP **8.4**、HTTPS強制を設定。
- 公開ディレクトリは展開先の **`ticket-demo/public` のみ**。リポジトリルートや `ticket-demo` 自体は指定しません。
- `public/.htaccess` は配布物に含まれています。`/login/`・`/tickets/` は静的画面、`/api/*`・`/sanctum/*`・`/up` はLaravelが担当します。
- 常駐Node.js、queue worker、独自ドメインは不要です。

## 5. 公開前の確認

1. `/up` が200、`/login/` と `/tickets/` の直接読み込みが表示される。
2. 未ログインの `/api/projects` は401。ログインすると一覧・5枚のチケットが表示される。
3. DnDで状態を変更し、再読み込み後も保存されている。詳細編集・コメント追加・削除ができる。
4. ログアウト後は保護されたデータにアクセスできない。
5. `/api/auth/register` は403。OAuth redirectも403。`.env`、`composer.json`、ログが公開されていない。
6. スマートフォン幅でもログインとボードを操作できる。

初回のDB/HTTPS/Apache/MariaDB実接続は利用者アカウントでの確認が必要です。完了するまでREADMEに公開済みリンクを載せません。

## データの復旧と更新

共有デモの変更は自動で元に戻りません。初回は定期的に確認し、必要な場合だけバックアップから専用DBを復元します。`migrate:fresh` は全テーブルを削除するため、この手順では使用しません。新しい空のデモ専用DBへ切り替え、migration + DemoSeederで作り直す方法もあります。既存DBにSeederを再実行しても拒否されます。

更新時は新しいリリースディレクトリへ展開し、同じ専用DBとAPP_KEYを使い、依存導入・migration・cache作成後にWebの公開ディレクトリを切り替えます。既存DBへDemoSeederを再実行しません。以前のリリースとDBバックアップを保持し、問題時は両方を整合した状態に戻します。

## 確認した公式資料

- [プラン料金・容量・制限](https://help.alwaysdata.com/en/docs/admin-billing/billing/public-cloud-prices/)
- [Laravel hosting](https://www.alwaysdata.com/en/laravel-hosting/)
- [PHP設定](https://help.alwaysdata.com/en/docs/web-hosting/languages/php/configuration/)
- [Next.js static export](https://nextjs.org/docs/app/guides/static-exports)
- [useSearchParamsとSuspense](https://nextjs.org/docs/app/api-reference/functions/use-search-params)

料金・利用条件の確認日: 2026-10-27。ホスティング側の条件変更時は再確認してください。
