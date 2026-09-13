<?php

namespace Tests\Feature\Auth;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Socialite\Facades\Socialite;
use Laravel\Socialite\Two\User as SocialiteUser;
use Tests\TestCase;

class GoogleLoginTest extends TestCase
{
    use RefreshDatabase;

    public function test_verified_google_user_can_login(): void
    {
        $googleUser = new SocialiteUser;

        $googleUser->id = 'google-user-123';
        $googleUser->name = 'Google User';
        $googleUser->email = 'google@example.com';
        $googleUser->user = [
            'email_verified' => true,
        ];

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($googleUser);

        $response = $this->get('/api/auth/google/callback');

        $response->assertRedirect('http://localhost:3000/tickets');

        $this->assertAuthenticated();

        $this->assertDatabaseHas('users', [
            'email' => 'google@example.com',
        ]);

        $this->assertDatabaseHas('social_accounts', [
            'provider' => 'google',
            'provider_user_id' => 'google-user-123',
            'provider_email' => 'google@example.com',
        ]);
    }

    public function test_verified_google_user_is_linked_to_existing_user(): void
    {
        $user = \App\Models\User::factory()->create([
            'email' => 'google@example.com',
            'email_verified_at' => null,
        ]);

        $googleUser = new SocialiteUser;

        $googleUser->id = 'google-user-123';
        $googleUser->name = 'Google User';
        $googleUser->email = 'google@example.com';
        $googleUser->user = [
            'email_verified' => true,
        ];

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($googleUser);

        $response = $this->get('/api/auth/google/callback');

        $response->assertRedirect('http://localhost:3000/tickets');

        $this->assertAuthenticatedAs($user);

        $this->assertDatabaseCount('users', 1);

        $this->assertDatabaseHas('social_accounts', [
            'user_id' => $user->id,
            'provider' => 'google',
            'provider_user_id' => 'google-user-123',
        ]);

        $this->assertNotNull($user->fresh()->email_verified_at);
    }

    public function test_existing_google_account_can_login(): void
    {
        $user = \App\Models\User::factory()->create([
            'email' => 'google@example.com',
            'email_verified_at' => now(),
        ]);

        \App\Models\SocialAccount::create([
            'user_id' => $user->id,
            'provider' => 'google',
            'provider_user_id' => 'google-user-123',
            'provider_email' => 'google@example.com',
        ]);

        $googleUser = new SocialiteUser;

        $googleUser->id = 'google-user-123';
        $googleUser->name = 'Google User';
        $googleUser->email = 'google@example.com';

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($googleUser);

        $response = $this->get('/api/auth/google/callback');

        $response->assertRedirect('http://localhost:3000/tickets');

        $this->assertAuthenticatedAs($user);

        $this->assertDatabaseCount('users', 1);
        $this->assertDatabaseCount('social_accounts', 1);
    }    

    public function test_google_login_redirects_with_error_when_email_is_missing(): void
    {
        $googleUser = new SocialiteUser;

        $googleUser->id = 'google-user-123';
        $googleUser->name = 'Google User';
        $googleUser->email = null;

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($googleUser);

        $response = $this->get('/api/auth/google/callback');

        $response->assertRedirect(
            'http://localhost:3000/login?error=google_email_missing'
        );

        $this->assertGuest();
        $this->assertDatabaseCount('users', 0);
        $this->assertDatabaseCount('social_accounts', 0);
    }

    public function test_google_login_redirects_with_error_when_email_is_unverified(): void
    {
        $googleUser = new SocialiteUser;

        $googleUser->id = 'google-user-123';
        $googleUser->name = 'Google User';
        $googleUser->email = 'google@example.com';
        $googleUser->user = [
            'email_verified' => false,
        ];

        Socialite::shouldReceive('driver->user')
            ->once()
            ->andReturn($googleUser);

        $response = $this->get('/api/auth/google/callback');

        $response->assertRedirect(
            'http://localhost:3000/login?error=google_email_unverified'
        );

        $this->assertGuest();
        $this->assertDatabaseCount('users', 0);
        $this->assertDatabaseCount('social_accounts', 0);
    }

}