<?php

namespace Tests\Feature\Auth;

use App\Models\User;
use Illuminate\Auth\Notifications\VerifyEmail;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Notification;
use Tests\TestCase;

class RegisterTest extends TestCase
{
    use RefreshDatabase;

    /**
     * 正しい入力内容で新規会員登録し、認証メールが送信されること
     */
    public function test_user_can_register_with_valid_data(): void
    {
        Notification::fake();

        $response = $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->postJson('/api/auth/register', [
                'name' => 'test',
                'email' => 'test@example.com',
                'password' => 'password123',
                'password_confirmation' => 'password123',
            ]);

        $response
            ->assertStatus(201)
            ->assertJsonPath('user.name', 'test')
            ->assertJsonPath('user.email', 'test@example.com')
            ->assertJsonPath('user.status', 'active')
            ->assertJsonStructure([
                'message',
                'user' => [
                    'id',
                    'name',
                    'email',
                    'status',
                    'createdAt',
                ],
            ]);

        $user = User::where('email', 'test@example.com')->firstOrFail();

        $this->assertNull($user->email_verified_at);

        Notification::assertSentTo(
            $user,
            VerifyEmail::class,
        );

        // メール認証が完了するまではログイン状態にしない
        $this->assertGuest();
    }

    /**
     * 既に登録されているメールアドレスでは会員登録できないこと
     */
    public function test_user_cannot_register_with_duplicate_email(): void
    {
        // 既存ユーザーを作成
        User::factory()->create([
            'email' => 'test@example.com',
        ]);

        // 同じメールアドレスで会員登録
        $response = $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->postJson('/api/auth/register', [
                'name' => 'test',
                'email' => 'test@example.com',
                'password' => 'password123',
                'password_confirmation' => 'password123',
            ]);

        // バリデーションエラーになることを確認
        $response
            ->assertStatus(422)
            ->assertJsonValidationErrors(['email']);
    }

    /**
     * パスワードが8文字未満の場合、会員登録できないこと
     */
    public function test_user_cannot_register_with_short_password(): void
    {
        $response = $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->postJson('/api/auth/register', [
                'name' => 'test',
                'email' => 'test@example.com',
                'password' => '1234567',
                'password_confirmation' => '1234567',
            ]);

        $response
            ->assertStatus(422)
            ->assertJsonValidationErrors(['password']);

        // ユーザーがDBに登録されていないことを確認
        $this->assertDatabaseMissing('users', [
            'email' => 'test@example.com',
        ]);
    }

    /**
     * 会員登録の試行回数が上限を超えた場合、429が返されること
     */
    public function test_register_is_rate_limited(): void
    {
        for ($i = 0; $i < 3; $i++) {
            $this->postJson('/api/auth/register', [
                'name' => 'test',
                'email' => "test{$i}@example.com",
                'password' => '1234567',
                'password_confirmation' => '1234567',
            ])->assertStatus(422);
        }

        $this->postJson('/api/auth/register', [
            'name' => 'test',
            'email' => 'test3@example.com',
            'password' => '1234567',
            'password_confirmation' => '1234567',
        ])->assertStatus(429);
    }

    /**
     * 数字を含まないパスワードでは登録できないこと
     */
    public function test_register_requires_password_with_number(): void
    {
        $response = $this->postJson('/api/auth/register', [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => 'password',
            'password_confirmation' => '1234567',
        ]);

        $response->assertStatus(422)
            ->assertJsonValidationErrors(['password']);
    }

    /**
     * 英字を含まないパスワードでは登録できないこと
     */
    public function test_register_requires_password_with_letter(): void
    {
        $this->postJson('/api/auth/register', [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => '12345678',
            'password_confirmation' => '1234567',
        ])
            ->assertStatus(422)
            ->assertJsonValidationErrors(['password']);
    }

    /**
     * 確認用パスワードが一致しない場合は登録できないこと
     */
    public function test_user_cannot_register_when_password_confirmation_does_not_match(): void
    {
        $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->postJson('/api/auth/register', [
                'name' => 'Test User',
                'email' => 'test@example.com',
                'password' => 'password123',
                'password_confirmation' => 'different123',
            ])
            ->assertStatus(422)
            ->assertJsonValidationErrors(['password']);

        $this->assertDatabaseMissing('users', [
            'email' => 'test@example.com',
        ]);
    }
}
