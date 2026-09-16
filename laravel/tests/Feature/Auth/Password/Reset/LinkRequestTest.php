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
     * 인증이 완료된 활성 이메일 계정에 비밀번호 재설정 메일을 보낼 수 있는지 확인한다.
     */
    public function test_verified_active_email_user_can_request_password_reset_link(): void
    {
        // 실제 메일을 발송하지 않고 알림 발송 여부만 검사한다.
        Notification::fake();

        // 비밀번호 로그인이 가능한 인증 완료·활성 사용자를 준비한다.
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
     * 등록되지 않은 이메일도 계정 존재 여부를 알 수 없는 동일한 응답을 반환한다.
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
     * 이메일 미인증 계정에는 비밀번호 재설정 메일을 보내지 않는다.
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
     * 정지된 계정에는 비밀번호 재설정 메일을 보내지 않는다.
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
     * 비밀번호가 없는 계정에는 비밀번호 재설정 메일을 보내지 않는다.
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
     * 비밀번호 재설정 메일 요청 횟수가 제한되는지 확인한다.
     */
    public function test_password_reset_request_is_rate_limited(): void
    {
        Notification::fake();

        // 허용된 3번의 요청은 정상 처리된다.
        for ($i = 0; $i < 3; $i++) {
            $this->postJson('/api/auth/forgot-password', [
                'email' => 'unknown@example.com',
            ])->assertOk();
        }

        // 같은 출처의 네 번째 요청은 거절된다.
        $this->postJson('/api/auth/forgot-password', [
            'email' => 'unknown@example.com',
        ])->assertStatus(429);

        Notification::assertNothingSent();
    }

    /**
     * 비밀번호 재설정 메일이 Next.js 재설정 화면을 가리키는지 확인한다.
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
