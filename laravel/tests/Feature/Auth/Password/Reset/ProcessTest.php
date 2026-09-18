<?php

namespace Tests\Feature\Auth\Password\Reset;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Password;
use Tests\TestCase;

class ProcessTest extends TestCase
{
    use RefreshDatabase;

    /**
     * 유효한 재설정 토큰으로 새 비밀번호를 저장할 수 있는지 확인한다.
     */
    public function test_user_can_reset_password_with_valid_token(): void
    {
        $user = User::factory()->create([
            'email' => 'reset@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $token = Password::broker()->createToken($user);

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => $token,
            'password' => 'NewPassword123',
            'password_confirmation' => 'NewPassword123',
        ])
            ->assertOk()
            ->assertJson([
                'message' => 'パスワードを再設定しました。新しいパスワードでログインしてください。',
            ]);

        $this->assertTrue(
            Hash::check(
                'NewPassword123',
                $user->fresh()->password,
            )
        );
    }

    /**
     * 잘못된 재설정 토큰으로는 비밀번호를 변경할 수 없다.
     */
    public function test_user_cannot_reset_password_with_invalid_token(): void
    {
        $user = User::factory()->create([
            'email' => 'invalid-token@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => 'invalid-token',
            'password' => 'NewPassword123',
            'password_confirmation' => 'NewPassword123',
        ])
            ->assertStatus(422)
            ->assertJson([
                'message' => 'メールアドレスまたは再設定トークンが正しくないか、有効期限が切れています。',
            ]);

        $this->assertTrue(
            Hash::check(
                'OldPassword123',
                $user->fresh()->password,
            )
        );
    }

    /**
     * 이미 사용한 재설정 토큰은 다시 사용할 수 없다.
     */
    public function test_password_reset_token_cannot_be_reused(): void
    {
        $user = User::factory()->create([
            'email' => 'used-token@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $token = Password::broker()->createToken($user);

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => $token,
            'password' => 'FirstPassword123',
            'password_confirmation' => 'FirstPassword123',
        ])->assertOk();

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => $token,
            'password' => 'SecondPassword123',
            'password_confirmation' => 'SecondPassword123',
        ])
            ->assertStatus(422)
            ->assertJson([
                'message' => 'メールアドレスまたは再設定トークンが正しくないか、有効期限が切れています。',
            ]);

        $this->assertTrue(
            Hash::check(
                'FirstPassword123',
                $user->fresh()->password,
            )
        );
    }

    /**
     * 토큰 발급 후 계정이 정지되면 비밀번호를 재설정할 수 없다.
     */
    public function test_suspended_user_cannot_reset_password_with_issued_token(): void
    {
        $user = User::factory()->create([
            'email' => 'suspended-after-token@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $token = Password::broker()->createToken($user);

        $user->forceFill([
            'status' => 'suspended',
        ])->save();

        $this->assertSame(
            'suspended',
            $user->fresh()->status,
        );

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => $token,
            'password' => 'NewPassword123',
            'password_confirmation' => 'NewPassword123',
        ])
            ->assertStatus(422)
            ->assertJson([
                'message' => 'メールアドレスまたは再設定トークンが正しくないか、有効期限が切れています。',
            ]);

        $this->assertTrue(
            Hash::check(
                'OldPassword123',
                $user->fresh()->password,
            )
        );
    }

    /**
     * 유효기간이 지난 토큰으로는 비밀번호를 재설정할 수 없다.
     */
    public function test_user_cannot_reset_password_with_expired_token(): void
    {
        $user = User::factory()->create([
            'email' => 'expired-token@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $token = Password::broker()->createToken($user);

        $expirationMinutes = (int) config(
            'auth.passwords.users.expire'
        );

        $this->travel($expirationMinutes + 1)->minutes();

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => $token,
            'password' => 'NewPassword123',
            'password_confirmation' => 'NewPassword123',
        ])
            ->assertStatus(422)
            ->assertJson([
                'message' => 'メールアドレスまたは再設定トークンが正しくないか、有効期限が切れています。',
            ]);

        $this->assertTrue(
            Hash::check(
                'OldPassword123',
                $user->fresh()->password,
            )
        );
    }

    /**
     * 비밀번호 재설정 시도 횟수가 제한되는지 확인한다.
     */
    public function test_password_reset_is_rate_limited(): void
    {
        $user = User::factory()->create([
            'email' => 'reset-rate-limit@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        // 다른 테스트의 요청 횟수와 겹치지 않도록 전용 IP를 사용한다.
        $this->withServerVariables([
            'REMOTE_ADDR' => '203.0.113.10',
        ]);

        // 잘못된 토큰이므로 컨트롤러는 422를 반환하지만 요청은 5회까지 허용된다.
        for ($i = 0; $i < 5; $i++) {
            $this->postJson('/api/auth/reset-password', [
                'email' => $user->email,
                'token' => 'invalid-token',
                'password' => 'NewPassword123',
                'password_confirmation' => 'NewPassword123',
            ])->assertStatus(422);
        }

        // 같은 출처의 여섯 번째 요청은 Rate Limit에 의해 차단된다.
        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => 'invalid-token',
            'password' => 'NewPassword123',
            'password_confirmation' => 'NewPassword123',
        ])->assertStatus(429);

        $this->assertTrue(
            Hash::check(
                'OldPassword123',
                $user->fresh()->password,
            )
        );
    }

    /**
     * 비밀번호 재설정 후 해당 사용자의 기존 세션만 삭제한다.
     */
    public function test_password_reset_invalidates_only_users_existing_sessions(): void
    {
        $user = User::factory()->create([
            'email' => 'session-reset@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $otherUser = User::factory()->create();

        DB::table('sessions')->insert([
            [
                'id' => 'reset-user-session',
                'user_id' => $user->id,
                'ip_address' => '127.0.0.1',
                'user_agent' => 'Password reset test',
                'payload' => '',
                'last_activity' => now()->timestamp,
            ],
            [
                'id' => 'other-user-session',
                'user_id' => $otherUser->id,
                'ip_address' => '127.0.0.2',
                'user_agent' => 'Other user test',
                'payload' => '',
                'last_activity' => now()->timestamp,
            ],
        ]);

        $token = Password::broker()->createToken($user);

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => $token,
            'password' => 'NewPassword123',
            'password_confirmation' => 'NewPassword123',
        ])->assertOk();

        $this->assertDatabaseMissing('sessions', [
            'id' => 'reset-user-session',
            'user_id' => $user->id,
        ]);

        $this->assertDatabaseHas('sessions', [
            'id' => 'other-user-session',
            'user_id' => $otherUser->id,
        ]);
    }
}
