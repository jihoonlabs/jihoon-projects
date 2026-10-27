#!/bin/sh
set -eu

PORT="${PORT:-10000}"
case "$PORT" in
    ''|*[!0-9]*) echo "PORT must be a numeric TCP port." >&2; exit 1 ;;
esac
sed -i "s/8080/${PORT}/g" /etc/apache2/ports.conf /etc/apache2/sites-available/000-default.conf

mkdir -p /data storage/app/private storage/app/public \
    storage/framework/cache/data storage/framework/sessions \
    storage/framework/views storage/logs bootstrap/cache

export APP_ENV=production
export APP_DEBUG=false
export TICKET_DEMO_MODE=true
export DB_CONNECTION=sqlite
export DB_DATABASE="${DB_DATABASE:-/data/database.sqlite}"
export SESSION_DRIVER=file
export SESSION_DOMAIN=null
export SESSION_SECURE_COOKIE=true
export SESSION_HTTP_ONLY=true
export SESSION_SAME_SITE=lax
export CACHE_STORE=file
export QUEUE_CONNECTION=sync
export MAIL_MAILER=log
export LOG_CHANNEL=stderr

PUBLIC_HOSTNAME="${RAILWAY_PUBLIC_DOMAIN:-${RENDER_EXTERNAL_HOSTNAME:-}}"
if [ -n "$PUBLIC_HOSTNAME" ]; then
    export APP_URL="https://$PUBLIC_HOSTNAME"
    export FRONTEND_URL="https://$PUBLIC_HOSTNAME"
    export SANCTUM_STATEFUL_DOMAINS="$PUBLIC_HOSTNAME"
fi

if [ ! -f "$DB_DATABASE" ]; then
    mkdir -p "$(dirname "$DB_DATABASE")"
    touch "$DB_DATABASE"
fi

if [ -z "${APP_KEY:-}" ]; then
    if [ ! -s /data/app.key ]; then
        php artisan key:generate --show --no-interaction > /data/app.key
    fi
    export APP_KEY="$(cat /data/app.key)"
fi

chown -R www-data:www-data /data storage bootstrap/cache
php artisan config:clear
php artisan migrate --force

if [ ! -f /data/demo-seeded ]; then
    php artisan db:seed --class=DemoSeeder --force
    touch /data/demo-seeded
    chown www-data:www-data /data/demo-seeded
fi

php artisan config:cache
exec apache2-foreground
