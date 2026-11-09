<?php

namespace App\Support;

use Illuminate\Http\Request;

/**
 * 同じLaravel APIを共有する複数フロントエンド（React・Vue）の戻り先URLを解決する。
 * リダイレクト先は設定済みの許可リストからのみ選び、外部URLへの遷移を防ぐ。
 */
final class FrontendUrl
{
    /**
     * 許可されたフロントエンド（キー => ベースURL）。未設定のURLは除外する。
     *
     * @return array<string, string>
     */
    public static function clients(): array
    {
        $clients = [];

        foreach ((array) config('services.frontend.clients', []) as $key => $url) {
            if (is_string($key) && is_string($url) && $url !== '') {
                $clients[$key] = rtrim($url, '/');
            }
        }

        return $clients;
    }

    /**
     * 既定のフロントエンドURL。判別できない要求はここへ戻す。
     */
    public static function default(): string
    {
        return rtrim((string) config('services.frontend.url'), '/');
    }

    /**
     * 許可リストにあるキーだけを返す。
     */
    public static function clientKey(mixed $key): ?string
    {
        return is_string($key) && array_key_exists($key, self::clients())
            ? $key
            : null;
    }

    /**
     * リクエストのOriginに一致するフロントエンドのキーを返す。
     */
    public static function clientKeyForOrigin(?string $origin): ?string
    {
        if ($origin === null || $origin === '') {
            return null;
        }

        $origin = strtolower(rtrim($origin, '/'));

        foreach (self::clients() as $key => $url) {
            if (strtolower($url) === $origin) {
                return $key;
            }
        }

        return null;
    }

    /**
     * キーに対応するURL。未知のキーは既定URLにする。
     */
    public static function forClient(mixed $key): string
    {
        $key = self::clientKey($key);

        return $key === null ? self::default() : self::clients()[$key];
    }

    /**
     * 要求元のOriginに対応するURL。一致しなければ既定URLにする。
     */
    public static function forRequest(Request $request): string
    {
        return self::forClient(
            self::clientKeyForOrigin($request->headers->get('Origin'))
        );
    }

    /**
     * 既定以外のフロントエンドから来た要求なら、そのキーを返す。
     * 既定フロントエンドのURL・リンクは従来と同じ形に保つ。
     */
    public static function nonDefaultClientKeyForRequest(Request $request): ?string
    {
        $key = self::clientKeyForOrigin($request->headers->get('Origin'));

        if ($key === null || self::clients()[$key] === self::default()) {
            return null;
        }

        return $key;
    }
}
