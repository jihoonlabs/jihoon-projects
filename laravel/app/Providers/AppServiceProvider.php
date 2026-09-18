<?php

namespace App\Providers;

use Illuminate\Auth\Notifications\ResetPassword;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\ServiceProvider;
use SocialiteProviders\Line\Provider as LineProvider;
use SocialiteProviders\Manager\SocialiteWasCalled;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        ResetPassword::createUrlUsing(
            function (object $notifiable, string $token): string {
                $query = http_build_query([
                    'token' => $token,
                    'email' => $notifiable->getEmailForPasswordReset(),
                ], encoding_type: PHP_QUERY_RFC3986);

                return rtrim(
                    (string) config('services.frontend.url'),
                    '/'
                ).'/reset-password?'.$query;
            }
        );

        Event::listen(function (SocialiteWasCalled $event) {
            $event->extendSocialite('line', LineProvider::class);
        });
    }
}
