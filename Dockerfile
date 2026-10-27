FROM node:22-bookworm-slim AS frontend-build

WORKDIR /workspace/react
RUN corepack enable && corepack prepare pnpm@11.25.0 --activate

COPY react/package.json react/pnpm-lock.yaml react/pnpm-workspace.yaml ./
COPY react/ ./

ENV TICKET_STATIC_EXPORT=true \
    NEXT_PUBLIC_API_URL= \
    NEXT_PUBLIC_DEMO_MODE=true

RUN pnpm install --frozen-lockfile && pnpm build

FROM php:8.4-apache-bookworm AS app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libicu-dev libonig-dev libsqlite3-dev libxml2-dev libzip-dev \
    && docker-php-ext-install bcmath dom intl mbstring pdo_sqlite xml xmlwriter zip \
    && a2enmod rewrite headers \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer

WORKDIR /var/www/html
COPY laravel/ ./
RUN composer install --no-dev --prefer-dist --no-interaction --optimize-autoloader

# Serve the static Next.js export and Laravel API from one HTTPS origin.
COPY --from=frontend-build /workspace/react/out/ ./public/
COPY deploy/render/apache-vhost.conf /etc/apache2/sites-available/000-default.conf
COPY deploy/render/apache-ports.conf /etc/apache2/ports.conf
COPY deploy/render/entrypoint.sh /usr/local/bin/ticket-demo-entrypoint

RUN chmod +x /usr/local/bin/ticket-demo-entrypoint \
    && mkdir -p /data storage/app/private storage/app/public \
        storage/framework/cache/data storage/framework/sessions \
        storage/framework/views storage/logs bootstrap/cache \
    && chown -R www-data:www-data storage bootstrap/cache /data

EXPOSE 10000
ENTRYPOINT ["/usr/local/bin/ticket-demo-entrypoint"]
