<?php

namespace Tests\Feature\Auth\Password\Reset;

use App\Models\User;
use Illuminate\Auth\Notifications\ResetPassword;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Notification;
use Tests\TestCase;

class LinkRequestTest extends TestCase
{
    use RefreshDatabase;

    /**
     * 認証済み・有効なユーザーにパスワード再設定メールが送信されることを確認
     */
    public function test_verified_active_email_user_can_request_password_reset_link(): void
    {
        // 実際のメール送信は行わず、通知の発行のみテスト
        Notification::fake();

        // ログイン可能な認証済み・有効なユーザーを作成
        $user = User::factory()->create([
            'email' => 'verified@example.com',
            'password' => Hash::make('Password123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $this->postJson('/api/auth/forgot-password', [
            'email' => $user->email,
        ])
            ->assertOk()
            ->assertJson([
                'message' => '入力されたメールアドレスが登録されている場合、パスワード再設定メールを送信しました。',
            ]);

        Notification::assertSentTo(
            $user,
            ResetPassword::class,
        );
    }

    /**
     * 未登録のメールアドレスでも存在有無を特定できない同一のレスポンスを返すことを確認
     */
    public function test_password_reset_request_does_not_reveal_unregistered_email(): void
    {
        Notification::fake();

        $this->postJson('/api/auth/forgot-password', [
            'email' => 'unknown@example.com',
        ])
            ->assertOk()
            ->assertJson([
                'message' => '入力されたメールアドレスが登録されている場合、パスワード再設定メールを送信しました。',
            ]);

        Notification::assertNothingSent();
    }

    /**
     * メール未認証のユーザーには再設定メールを送信しないことを確認
     */
    public function test_password_reset_link_is_not_sent_to_unverified_user(): void
    {
        Notification::fake();

        $user = User::factory()->unverified()->create([
            'email' => 'unverified@example.com',
            'password' => Hash::make('Password123'),
            'status' => 'active',
        ]);

        $this->postJson('/api/auth/forgot-password', [
            'email' => $user->email,
        ])
            ->assertOk()
            ->assertJson([
                'message' => '入力されたメールアドレスが登録されている場合、パスワード再設定メールを送信しました。',
            ]);

        Notification::assertNothingSent();
    }

    /**
     * 停止中のユーザーには再設定メールを送信しないことを確認
     */
    public function test_password_reset_link_is_not_sent_to_suspended_user(): void
    {
        Notification::fake();

        $user = User::factory()->create([
            'email' => 'suspended@example.com',
            'password' => Hash::make('Password123'),
            'email_verified_at' => now(),
            'status' => 'suspended',
        ]);

        $this->postJson('/api/auth/forgot-password', [
            'email' => $user->email,
        ])
            ->assertOk()
            ->assertJson([
                'message' => '入力されたメールアドレスが登録されている場合、パスワード再設定メールを送信しました。',
            ]);

        Notification::assertNothingSent();
    }

    /**
     * パスワード未設定(ソーシャルログイン専用)のユーザーには再設定メールを送信しないことを確認
     */
    public function test_password_reset_link_is_not_sent_to_user_without_password(): void
    {
        Notification::fake();

        $user = User::factory()->create([
            'email' => 'social@example.com',
            'password' => null,
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $this->postJson('/api/auth/forgot-password', [
            'email' => $user->email,
        ])
            ->assertOk()
            ->assertJson([
                'message' => '入力されたメールアドレスが登録されている場合、パスワード再設定メールを送信しました。',
            ]);

        Notification::assertNothingSent();
    }

    /**
     * パスワード再設定のリクエスト制限(Rate Limit)が機能することを確認
     */
    public function test_password_reset_request_is_rate_limited(): void
    {
        Notification::fake();

        // 許容される3回のリクエストは正常処理
        for ($i = 0; $i < 3; $i++) {
            $this->postJson('/api/auth/forgot-password', [
                'email' => 'unknown@example.com',
            ])->assertOk();
        }

        // 4回目のリクエストはレート制限(429)で拒否
        $this->postJson('/api/auth/forgot-password', [
            'email' => 'unknown@example.com',
        ])->assertStatus(429);

        Notification::assertNothingSent();
    }

    /**
     * 再設定メールのURLがフロントエンドのURL構造に従っていることを確認
     */
    public function test_password_reset_notification_uses_frontend_url(): void
    {
        Notification::fake();

        $user = User::factory()->create([
            'email' => 'reset-url@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $this->postJson('/api/auth/forgot-password', [
            'email' => $user->email,
        ])->assertOk();

        Notification::assertSentTo(
            $user,
            ResetPassword::class,
            function (ResetPassword $notification) use ($user): bool {
                $url = $notification->toMail($user)->actionUrl;

                $this->assertStringStartsWith(
                    rtrim(
                        (string) config('services.frontend.url'),
                        '/'
                    ).'/reset-password?',
                    $url,
                );

                parse_str(
                    (string) parse_url($url, PHP_URL_QUERY),
                    $query,
                );

                $this->assertSame(
                    $notification->token,
                    $query['token'] ?? null,
                );

                $this->assertSame(
                    $user->email,
                    $query['email'] ?? null,
                );

                return true;
            },
        );
    }
}
