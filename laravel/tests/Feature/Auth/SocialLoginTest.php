<?php

namespace Tests\Feature\Auth;

use App\Models\SocialAccount;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Socialite\Facades\Socialite;
use Laravel\Socialite\Two\User as SocialiteUser;
use RuntimeException;
use Tests\TestCase;

class SocialLoginTest extends TestCase
{
    use RefreshDatabase;

    /**
     * Google認証で新規ユーザーとしてログインできること
     */

    public function test_google_user_can_login(): void
    {
        $socialUser = new SocialiteUser;

        $socialUser->id = 'google-user-123';
        $socialUser->name = 'Google User';
        $socialUser->email = 'google@example.com';

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($socialUser);

        $response = $this->get('/api/auth/google/callback');

        $response->assertRedirect('http://localhost:3000/tickets');

        $this->assertAuthenticated();

        $this->assertDatabaseHas('users', [
            'name' => 'Google User',
            'email' => null,
            'password' => null,
        ]);

        $this->assertDatabaseHas('social_accounts', [
            'provider' => 'google',
            'provider_user_id' => 'google-user-123',
            'provider_email' => 'google@example.com',
        ]);
    }

    /**
     * メールアドレスが取得できないLINEユーザーでもログインできること
     */

    public function test_line_user_can_login_without_email(): void
    {
        $socialUser = new SocialiteUser;

        $socialUser->id = 'line-user-123';
        $socialUser->name = 'LINE User';
        $socialUser->email = null;

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($socialUser);

        $response = $this->get('/api/auth/line/callback');

        $response->assertRedirect('http://localhost:3000/tickets');

        $this->assertAuthenticated();

        $this->assertDatabaseHas('users', [
            'name' => 'LINE User',
            'email' => null,
            'password' => null,
        ]);

        $this->assertDatabaseHas('social_accounts', [
            'provider' => 'line',
            'provider_user_id' => 'line-user-123',
            'provider_email' => null,
        ]);
    }

    /**
     * 既存のソーシャルアカウントで同じユーザーとしてログインできること
     */    

    public function test_existing_social_account_can_login(): void
    {
        $user = User::factory()->create();

        SocialAccount::create([
            'user_id' => $user->id,
            'provider' => 'google',
            'provider_user_id' => 'google-user-123',
            'provider_email' => 'google@example.com',
        ]);

        $socialUser = new SocialiteUser;

        $socialUser->id = 'google-user-123';
        $socialUser->name = 'Google User';
        $socialUser->email = 'google@example.com';

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($socialUser);

        $response = $this->get('/api/auth/google/callback');

        $response->assertRedirect('http://localhost:3000/tickets');

        $this->assertAuthenticatedAs($user);
        $this->assertDatabaseCount('users', 1);
        $this->assertDatabaseCount('social_accounts', 1);
    }

    /**
     * 同じメールアドレスでも既存ユーザーとは自動連携しないこと
     */

    public function test_social_user_is_not_automatically_linked_by_email(): void
    {
        $existingUser = User::factory()->create([
            'email' => 'same@example.com',
        ]);

        $socialUser = new SocialiteUser;

        $socialUser->id = 'google-user-123';
        $socialUser->name = 'Google User';
        $socialUser->email = 'same@example.com';

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($socialUser);

        $this->get('/api/auth/google/callback')
            ->assertRedirect('http://localhost:3000/tickets');

        $this->assertDatabaseCount('users', 2);

        $this->assertDatabaseHas('social_accounts', [
            'provider' => 'google',
            'provider_user_id' => 'google-user-123',
            'provider_email' => 'same@example.com',
        ]);

        $this->assertDatabaseMissing('social_accounts', [
            'user_id' => $existingUser->id,
            'provider' => 'google',
        ]);
    }


    /**
     * 未対応の認証プロバイダーは拒否されること
     */

    public function test_unsupported_provider_returns_404(): void
    {
        $this->get('/api/auth/facebook/callback')
            ->assertNotFound();
    }

    /**
     * OAuth認証に失敗した場合はログイン画面へ戻ること
     */
    public function test_social_login_failure_redirects_to_login(): void
    {
        Socialite::shouldReceive('driver->user')
            ->once()
            ->andThrow(new RuntimeException('OAuth failed'));

        $response = $this->get('/api/auth/google/callback');

        $response->assertRedirect(
            'http://localhost:3000/login?error=social_login_failed&provider=google'
        );

        $this->assertGuest();
        $this->assertDatabaseCount('users', 0);
        $this->assertDatabaseCount('social_accounts', 0);
    }

    /**
     * 停止中のソーシャルアカウントはログインできないこと
     */
    public function test_suspended_social_account_cannot_login(): void
    {
        $user = User::factory()->create([
            'status' => 'suspended',
        ]);

        SocialAccount::create([
            'user_id' => $user->id,
            'provider' => 'google',
            'provider_user_id' => 'google-user-123',
            'provider_email' => 'google@example.com',
        ]);

        $socialUser = new SocialiteUser;
        $socialUser->id = 'google-user-123';
        $socialUser->name = 'Google User';
        $socialUser->email = 'google@example.com';

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($socialUser);

        $response = $this->get('/api/auth/google/callback');

        $response->assertRedirect(
            'http://localhost:3000/login?error=account_unavailable&provider=google'
        );

        $this->assertGuest();
    }
}