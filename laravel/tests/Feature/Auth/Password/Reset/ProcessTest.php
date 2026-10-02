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

        // トークンの有効期限(分)を検証するため時間を進める
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

    public function test_password_reset_is_rate_limited(): void
    {
        $user = User::factory()->create([
            'email' => 'reset-rate-limit@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        // 他テストとリクエスト数が重複しないよう専用IPを指定
        $this->withServerVariables([
            'REMOTE_ADDR' => '203.0.113.10',
        ]);

        for ($i = 0; $i < 5; $i++) {
            $this->postJson('/api/auth/reset-password', [
                'email' => $user->email,
                'token' => 'invalid-token',
                'password' => 'NewPassword123',
                'password_confirmation' => 'NewPassword123',
            ])->assertStatus(422);
        }

        // 6回目のリクエストでレート制限(429)が発生することを確認
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
