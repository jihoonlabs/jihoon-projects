<?php

namespace Tests\Feature\Auth;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Tests\TestCase;

class LoginTest extends TestCase
{
    use RefreshDatabase;

    /**
     * 正しいメールアドレスとパスワードでログインできること
     */
    public function test_user_can_login_with_valid_credentials(): void
    {
        // テスト用ユーザーを作成
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123'),
        ]);

        // ログインAPIを実行
        $response = $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->postJson('/api/auth/login', [
                'email' => 'test@example.com',
                'password' => 'password123',
            ]);

        // ログイン成功を確認
        $response
            ->assertStatus(200)
            ->assertJsonPath('user.id', $user->id)
            ->assertJsonPath('user.email', 'test@example.com');

        // Laravelのセッションで認証されていることを確認
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
            'password' => Hash::make('password123'),
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
        // テスト用ユーザーを作成
        $user = User::factory()->create();

        // ログイン状態にする
        $this->actingAs($user);

        // ログイン中のユーザー情報を取得
        $response = $this
            ->withHeader('Origin', 'http://localhost:3000')
            ->getJson('/api/auth/me');

        // ユーザー情報が取得できることを確認
        $response
            ->assertStatus(200)
            ->assertJsonPath('id', $user->id)
            ->assertJsonPath('email', $user->email);
    }

    /**
     * ログアウト後、認証状態が解除されること
     */
    public function test_authenticated_user_can_logout(): void
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123'),
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
}