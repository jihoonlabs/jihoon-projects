<?php

namespace Tests\Feature\Auth;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class LoginTest extends TestCase
{
    use RefreshDatabase;

    /**
     * 正しいメールアドレスとパスワードでログインできること
     */
    public function test_user_can_login_with_valid_credentials(): void
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => 'password123',
        ]);

        $response = $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->postJson('/api/auth/login', [
                'email' => 'test@example.com',
                'password' => 'password123',
            ]);

        $response
            ->assertStatus(200)
            ->assertJsonPath('user.id', $user->id)
            ->assertJsonPath('user.name', $user->name)
            ->assertJsonPath('user.email', $user->email)
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

        $this->assertAuthenticatedAs($user);
    }

    /**
     * パスワードが間違っている場合、ログインできないこと
     */
    public function test_user_cannot_login_with_invalid_password(): void
    {
        // テスト用ユーザーを作成
        User::factory()->create([
            'email' => 'test@example.com',
           'password' => 'password123',
        ]);

        // 間違ったパスワードでログイン
        $response = $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->postJson('/api/auth/login', [
                'email' => 'test@example.com',
                'password' => 'wrongpassword',
            ]);

        // バリデーションエラーになることを確認
        $response->assertStatus(422);

        // 認証されていないことを確認
        $this->assertGuest();
    }

    /**
     * ログイン後、認証中のユーザー情報を取得できること
     */
    public function test_authenticated_user_can_get_own_information(): void
    {
        $user = User::factory()->create();

        // ログイン状態にする
        $this->actingAs($user);

        $response = $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->getJson('/api/auth/me');

        $response
            ->assertStatus(200)
            ->assertJsonPath('id', $user->id)
            ->assertJsonPath('name', $user->name)
            ->assertJsonPath('email', $user->email)
            ->assertJsonPath('status', 'active')
            ->assertJsonStructure([
                'id',
                'name',
                'email',
                'status',
                'createdAt',
            ]);
    }

    /**
     * ログイン済みでも停止中のユーザーは認証必須APIにアクセスできないこと
     */
    public function test_suspended_authenticated_user_cannot_access_protected_api(): void
    {
        $user = User::factory()->create([
            'status' => 'suspended',
        ]);

        $this->actingAs($user);

        $this->getJson('/api/auth/me')
            ->assertStatus(403);

        $this->assertGuest();
    }
    
    /**
     * 未認証ユーザーは認証必須APIにアクセスできないこと
     */
    public function test_guest_cannot_access_me(): void
    {
        $this->getJson('/api/auth/me')
            ->assertStatus(401);
    }

    /**
     * ログアウト後、認証状態が解除されること
     */
    public function test_authenticated_user_can_logout(): void
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
           'password' => 'password123',
        ]);

        // 実際のログインAPIでログイン
        $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->postJson('/api/auth/login', [
                'email' => 'test@example.com',
                'password' => 'password123',
            ])
            ->assertStatus(200);

        // ログアウト
        $response = $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->postJson('/api/auth/logout');

        $response->assertStatus(200);

        // テスト内で保持されている認証Guardのキャッシュをリセット
        $this->app['auth']->forgetGuards();

        // ログアウト後、認証が必要なAPIにアクセスできないことを確認
        $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->getJson('/api/auth/me')
            ->assertStatus(401);
    }

    /**
     * ログイン試行回数が上限を超えた場合、429が返されること
     */
    public function test_login_is_rate_limited(): void
    {
        for ($i = 0; $i < 5; $i++) {
            $this->postJson('/api/auth/login', [
                'email' => 'test@example.com',
                'password' => 'wrongpassword',
            ])->assertStatus(422);
        }

        $this->postJson('/api/auth/login', [
            'email' => 'test@example.com',
            'password' => 'wrongpassword',
        ])->assertStatus(429);
    }

    /**
     * 停止中のユーザーはログインできないこと
     */
    public function test_suspended_user_cannot_login(): void
    {
        User::factory()->create([
            'email' => 'suspended@example.com',
            'password' => 'password123',
            'status' => 'suspended',
        ]);

        $this->postJson('/api/auth/login', [
            'email' => 'suspended@example.com',
            'password' => 'password123',
        ])
            ->assertStatus(422);

        $this->assertGuest();
    }
}