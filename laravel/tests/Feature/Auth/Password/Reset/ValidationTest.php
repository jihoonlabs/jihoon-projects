<?php

namespace Tests\Feature\Auth\Password\Reset;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Password;
use Tests\TestCase;

class ValidationTest extends TestCase
{
    use RefreshDatabase;

    /**
     * 비밀번호 확인값이 일치하지 않으면 재설정할 수 없다.
     */
    public function test_password_reset_requires_matching_confirmation(): void
    {
        $user = User::factory()->create([
            'email' => 'confirmation@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $token = Password::broker()->createToken($user);

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => $token,
            'password' => 'NewPassword123',
            'password_confirmation' => 'DifferentPassword123',
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors([
                'password',
            ]);

        $this->assertTrue(
            Hash::check(
                'OldPassword123',
                $user->fresh()->password,
            )
        );
    }

    /**
     * 8자보다 짧은 비밀번호로는 재설정할 수 없다.
     */
    public function test_password_reset_rejects_short_password(): void
    {
        $user = User::factory()->create([
            'email' => 'short-password@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $token = Password::broker()->createToken($user);

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => $token,
            'password' => 'Pass123',
            'password_confirmation' => 'Pass123',
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors([
                'password',
            ]);

        $this->assertTrue(
            Hash::check(
                'OldPassword123',
                $user->fresh()->password,
            )
        );
    }

    /**
     * 숫자가 없는 비밀번호로는 재설정할 수 없다.
     */
    public function test_password_reset_requires_number(): void
    {
        $user = User::factory()->create([
            'email' => 'password-without-number@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $token = Password::broker()->createToken($user);

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => $token,
            'password' => 'OnlyLetters',
            'password_confirmation' => 'OnlyLetters',
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors([
                'password',
            ]);

        $this->assertTrue(
            Hash::check(
                'OldPassword123',
                $user->fresh()->password,
            )
        );
    }

    /**
     * 영문이 없는 비밀번호로는 재설정할 수 없다.
     */
    public function test_password_reset_requires_letter(): void
    {
        $user = User::factory()->create([
            'email' => 'password-without-letter@example.com',
            'password' => Hash::make('OldPassword123'),
            'email_verified_at' => now(),
            'status' => 'active',
        ]);

        $token = Password::broker()->createToken($user);

        $this->postJson('/api/auth/reset-password', [
            'email' => $user->email,
            'token' => $token,
            'password' => '12345678',
            'password_confirmation' => '12345678',
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors([
                'password',
            ]);

        $this->assertTrue(
            Hash::check(
                'OldPassword123',
                $user->fresh()->password,
            )
        );
    }
}
