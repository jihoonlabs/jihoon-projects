<?php

namespace App\Providers;

use App\Support\FrontendUrl;
use Illuminate\Auth\Notifications\ResetPassword;
use Illuminate\Auth\Notifications\VerifyEmail;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\URL;
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

                // 再設定を要求したフロントエンドの画面へ案内する
                return FrontendUrl::forRequest(request())
                    .'/reset-password?'.$query;
            }
        );

        VerifyEmail::createUrlUsing(function (object $notifiable): string {
            $parameters = [
                'id' => $notifiable->getKey(),
                'hash' => sha1($notifiable->getEmailForVerification()),
            ];

            // 認証後の戻り先を署名付きURLに含める。既定フロントエンドは従来どおりのURL。
            $client = FrontendUrl::nonDefaultClientKeyForRequest(request());

            if ($client !== null) {
                $parameters['client'] = $client;
            }

            return URL::temporarySignedRoute(
                'verification.verify',
                Carbon::now()->addMinutes(
                    Config::get('auth.verification.expire', 60)
                ),
                $parameters,
            );
        });

        Event::listen(function (SocialiteWasCalled $event) {
            $event->extendSocialite('line', LineProvider::class);
        });
    }
}
