<?php

namespace Tests\Feature\Auth;

use App\Models\User;
use Illuminate\Auth\Notifications\VerifyEmail;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Notification;
use Illuminate\Support\Facades\URL;
use Tests\TestCase;

class EmailVerificationTest extends TestCase
{
    use RefreshDatabase;

    /**
     * 有効な署名付きURLからメール認証を完了できること
     */
    public function test_user_can_verify_email_with_valid_signed_url(): void
    {
        $user = User::factory()->unverified()->create();

        $verificationUrl = URL::temporarySignedRoute(
            'verification.verify',
            now()->addMinutes(60),
            [
                'id' => $user->id,
                'hash' => sha1($user->getEmailForVerification()),
            ],
        );

        $this->get($verificationUrl)
            ->assertRedirect(
                'http://localhost:3000/login?verified=1'
            );

        $this->assertTrue(
            $user->fresh()->hasVerifiedEmail()
        );
    }

    /**
     * メールアドレスのハッシュが一致しない場合は認証できないこと
     */
    public function test_user_cannot_verify_email_with_invalid_hash(): void
    {
        $user = User::factory()->unverified()->create();

        $verificationUrl = URL::temporarySignedRoute(
            'verification.verify',
            now()->addMinutes(60),
            [
                'id' => $user->id,
                'hash' => sha1('different@example.com'),
            ],
        );

        $this->get($verificationUrl)
            ->assertForbidden();

        $this->assertFalse(
            $user->fresh()->hasVerifiedEmail()
        );
    }

    /**
     * 期限切れの署名付きURLではメール認証できないこと
     */
    public function test_user_cannot_verify_email_with_expired_signed_url(): void
    {
        $user = User::factory()->unverified()->create();

        $verificationUrl = URL::temporarySignedRoute(
            'verification.verify',
            now()->subMinute(),
            [
                'id' => $user->id,
                'hash' => sha1($user->getEmailForVerification()),
            ],
        );

        $this->get($verificationUrl)
            ->assertForbidden();

        $this->assertFalse(
            $user->fresh()->hasVerifiedEmail()
        );
    }

    /**
     * 未認証ユーザーに認証メールを再送できること
     */
    public function test_verification_email_can_be_resent(): void
    {
        Notification::fake();

        $user = User::factory()->unverified()->create([
            'email' => 'unverified@example.com',
        ]);

        $this->postJson('/api/auth/email/verification-notification', [
            'email' => 'unverified@example.com',
        ])
            ->assertOk()
            ->assertJson([
                'message' => '登録されている未認証のメールアドレスには認証メールを送信しました。',
            ]);

        Notification::assertSentTo(
            $user,
            VerifyEmail::class,
        );
    }

    /**
     * 未登録のメールアドレスでも同じレスポンスを返すこと
     */
    public function test_resend_does_not_reveal_unregistered_email(): void
    {
        Notification::fake();

        $this->postJson('/api/auth/email/verification-notification', [
            'email' => 'unknown@example.com',
        ])
            ->assertOk()
            ->assertJson([
                'message' => '登録されている未認証のメールアドレスには認証メールを送信しました。',
            ]);

        Notification::assertNothingSent();
    }

    /**
     * 認証済みユーザーには認証メールを再送しないこと
     */
    public function test_verification_email_is_not_resent_to_verified_user(): void
    {
        // 実際にはメールを送らず、通知の送信状況だけを記録する
        Notification::fake();

        // Factoryの通常状態はメール認証済み
        User::factory()->create([
            'email' => 'verified@example.com',
        ]);

        // 認証済みメールアドレスで再送を要求する
        $this->postJson('/api/auth/email/verification-notification', [
            'email' => 'verified@example.com',
        ])
            ->assertOk()
            ->assertJson([
                'message' => '登録されている未認証のメールアドレスには認証メールを送信しました。',
            ]);

        // 認証済みなので実際の通知は送信されない
        Notification::assertNothingSent();
    }

    /**
     * 認証メールの再送回数が制限されること
     */
    public function test_verification_email_resend_is_rate_limited(): void
    {
        Notification::fake();

        // 許可されている6回までは正常に処理される
        for ($i = 0; $i < 6; $i++) {
            $this->postJson('/api/auth/email/verification-notification', [
                'email' => 'unknown@example.com',
            ])->assertOk();
        }

        // 7回目のリクエストは拒否される
        $this->postJson('/api/auth/email/verification-notification', [
            'email' => 'unknown@example.com',
        ])->assertStatus(429);

        Notification::assertNothingSent();
    }
}
