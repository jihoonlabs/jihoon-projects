<?php

namespace Tests\Feature\Auth;

use App\Models\User;
use Illuminate\Auth\Notifications\ResetPassword;
use Illuminate\Auth\Notifications\VerifyEmail;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Notification;
use Laravel\Socialite\Facades\Socialite;
use Laravel\Socialite\Two\User as SocialiteUser;
use RuntimeException;
use Tests\TestCase;

/**
 * React・Vueの両フロントエンドが同じLaravel APIを共有できることを確認する。
 * テスト環境では FRONTEND_VUE_URL=http://localhost:3001 を phpunit.xml で設定している。
 */
class SharedFrontendTest extends TestCase
{
    use RefreshDatabase;

    private const REACT_URL = 'http://localhost:3000';

    private const VUE_URL = 'http://localhost:3001';

    /**
     * VueのOriginからのプリフライトをCookie付きで許可すること
     */
    public function test_cors_allows_vue_origin_with_credentials(): void
    {
        $this->withHeaders([
            'Origin' => self::VUE_URL,
            'Access-Control-Request-Method' => 'POST',
        ])->options('/api/auth/login')
            ->assertHeader('Access-Control-Allow-Origin', self::VUE_URL)
            ->assertHeader('Access-Control-Allow-Credentials', 'true');
    }

    /**
     * 許可リストにないOriginには許可ヘッダーを返さないこと
     */
    public function test_cors_rejects_unknown_origin(): void
    {
        $this->withHeaders([
            'Origin' => 'https://evil.example',
            'Access-Control-Request-Method' => 'POST',
        ])->options('/api/auth/login')
            ->assertHeaderMissing('Access-Control-Allow-Origin');
    }

    /**
     * VueのOriginからでもSanctumのセッションでログインできること
     */
    public function test_user_can_login_from_vue_origin(): void
    {
        $user = User::factory()->create([
            'email' => 'vue-login@example.com',
            'password' => 'password123',
        ]);

        $this->withHeader('Origin', self::VUE_URL)
            ->postJson('/api/auth/login', [
                'email' => 'vue-login@example.com',
                'password' => 'password123',
            ])
            ->assertOk()
            ->assertJsonPath('user.id', $user->id);

        $this->assertAuthenticatedAs($user);
    }

    /**
     * Vueから要求したパスワード再設定メールがVueの画面を指すこと
     */
    public function test_password_reset_link_points_to_vue_when_requested_from_vue(): void
    {
        Notification::fake();

        $user = $this->createPasswordUser('reset-vue@example.com');

        $this->withHeader('Origin', self::VUE_URL)
            ->postJson('/api/auth/forgot-password', [
                'email' => $user->email,
            ])
            ->assertOk();

        Notification::assertSentTo(
            $user,
            ResetPassword::class,
            function (ResetPassword $notification) use ($user): bool {
                $this->assertStringStartsWith(
                    self::VUE_URL.'/reset-password?',
                    $notification->toMail($user)->actionUrl,
                );

                return true;
            },
        );
    }

    /**
     * 許可リストにないOriginからの再設定メールは既定のフロントエンドを指すこと
     */
    public function test_password_reset_link_uses_default_for_unknown_origin(): void
    {
        Notification::fake();

        $user = $this->createPasswordUser('reset-unknown@example.com');

        $this->withHeader('Origin', 'https://evil.example')
            ->postJson('/api/auth/forgot-password', [
                'email' => $user->email,
            ])
            ->assertOk();

        Notification::assertSentTo(
            $user,
            ResetPassword::class,
            function (ResetPassword $notification) use ($user): bool {
                $this->assertStringStartsWith(
                    self::REACT_URL.'/reset-password?',
                    $notification->toMail($user)->actionUrl,
                );

                return true;
            },
        );
    }

    /**
     * Vueで登録した場合、認証リンクからVueのログイン画面へ戻ること
     */
    public function test_verification_link_returns_to_vue_after_vue_registration(): void
    {
        Notification::fake();

        $this->withHeader('Origin', self::VUE_URL)
            ->postJson('/api/auth/register', [
                'name' => 'vue user',
                'email' => 'register-vue@example.com',
                'password' => 'password123',
                'password_confirmation' => 'password123',
            ])
            ->assertCreated();

        $user = User::where('email', 'register-vue@example.com')->firstOrFail();
        $verificationUrl = $this->verificationUrlFor($user);

        $this->assertStringContainsString('client=vue', $verificationUrl);

        $this->get($verificationUrl)
            ->assertRedirect(self::VUE_URL.'/login?verified=1');

        $this->assertTrue($user->fresh()->hasVerifiedEmail());
    }

    /**
     * Reactで登録した場合の認証リンクは従来どおり戻り先を含まないこと
     */
    public function test_verification_link_from_react_keeps_existing_format(): void
    {
        Notification::fake();

        $this->withHeader('Origin', self::REACT_URL)
            ->postJson('/api/auth/register', [
                'name' => 'react user',
                'email' => 'register-react@example.com',
                'password' => 'password123',
                'password_confirmation' => 'password123',
            ])
            ->assertCreated();

        $user = User::where('email', 'register-react@example.com')->firstOrFail();
        $verificationUrl = $this->verificationUrlFor($user);

        $this->assertStringNotContainsString('client=', $verificationUrl);

        $this->get($verificationUrl)
            ->assertRedirect(self::REACT_URL.'/login?verified=1');
    }

    /**
     * 認証リンクの戻り先を書き換えると署名検証で拒否されること
     */
    public function test_verification_link_rejects_tampered_client(): void
    {
        Notification::fake();

        $this->withHeader('Origin', self::VUE_URL)
            ->postJson('/api/auth/register', [
                'name' => 'tamper user',
                'email' => 'register-tamper@example.com',
                'password' => 'password123',
                'password_confirmation' => 'password123',
            ])
            ->assertCreated();

        $user = User::where('email', 'register-tamper@example.com')->firstOrFail();
        $tamperedUrl = str_replace(
            'client=vue',
            'client=react',
            $this->verificationUrlFor($user),
        );

        $this->get($tamperedUrl)->assertForbidden();

        $this->assertFalse($user->fresh()->hasVerifiedEmail());
    }

    /**
     * Vueから開始したソーシャルログインは戻り先キーをセッションに保持すること
     */
    public function test_social_redirect_remembers_vue_client(): void
    {
        Socialite::shouldReceive('driver->redirect')
            ->once()
            ->andReturn(redirect('https://provider.example/authorize'));

        $this->get('/api/auth/google/redirect?client=vue')
            ->assertRedirect('https://provider.example/authorize')
            ->assertSessionHas('social_login_client', 'vue');
    }

    /**
     * 許可リストにない戻り先キーはセッションに保持しないこと
     */
    public function test_social_redirect_ignores_unknown_client(): void
    {
        Socialite::shouldReceive('driver->redirect')
            ->once()
            ->andReturn(redirect('https://provider.example/authorize'));

        $this->get('/api/auth/google/redirect?client=https://evil.example')
            ->assertRedirect('https://provider.example/authorize')
            ->assertSessionMissing('social_login_client');
    }

    /**
     * Vueから開始したソーシャルログインはVueのチケット画面へ戻ること
     */
    public function test_social_callback_returns_to_vue(): void
    {
        $socialUser = new SocialiteUser;

        $socialUser->id = 'google-vue-123';
        $socialUser->name = 'Google Vue User';
        $socialUser->email = 'google-vue@example.com';

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($socialUser);

        $this->withSession(['social_login_client' => 'vue'])
            ->get('/api/auth/google/callback')
            ->assertRedirect(self::VUE_URL.'/tickets')
            ->assertSessionMissing('social_login_client');

        $this->assertAuthenticated();
    }

    /**
     * Vueから開始したソーシャルログインの失敗はVueのログイン画面へ戻ること
     */
    public function test_social_callback_failure_returns_to_vue(): void
    {
        Socialite::shouldReceive('driver->user')
            ->once()
            ->andThrow(new RuntimeException('provider error'));

        $this->withSession(['social_login_client' => 'vue'])
            ->get('/api/auth/google/callback')
            ->assertRedirect(
                self::VUE_URL.'/login?error=social_login_failed&provider=google'
            );

        $this->assertGuest();
    }

    private function createPasswordUser(string $email): User
    {
        return User::factory()->create([
            'email' => $email,
            'password' => Hash::make('Password123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);
    }

    private function verificationUrlFor(User $user): string
    {
        $verificationUrl = null;

        Notification::assertSentTo(
            $user,
            VerifyEmail::class,
            function (VerifyEmail $notification) use ($user, &$verificationUrl): bool {
                $verificationUrl = $notification->toMail($user)->actionUrl;

                return true;
            },
        );

        return (string) $verificationUrl;
    }
}
