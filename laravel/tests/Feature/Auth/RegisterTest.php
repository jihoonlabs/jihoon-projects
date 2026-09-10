<?php

namespace Tests\Feature\Auth;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class RegisterTest extends TestCase
{
    use RefreshDatabase;

    /**
     * 正しい入力内容で新規会員登録できること
     */
    public function test_user_can_register_with_valid_data(): void
    {
        $response = $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->postJson('/api/auth/register', [
                'name' => 'test',
                'email' => 'test@example.com',
                'password' => 'password123',
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

        // ユーザーがDBに登録されていることを確認
        $this->assertDatabaseHas('users', [
            'email' => 'test@example.com',
            'status' => 'active',
        ]);

        // 登録後、そのままログイン状態になっていることを確認
        $this->assertAuthenticated();
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
            ]);

        $response
            ->assertStatus(422)
            ->assertJsonValidationErrors(['password']);

        // ユーザーがDBに登録されていないことを確認
        $this->assertDatabaseMissing('users', [
            'email' => 'test@example.com',
        ]);
    }

}