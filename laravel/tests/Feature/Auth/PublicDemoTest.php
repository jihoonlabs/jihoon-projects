<?php

namespace Tests\Feature\Auth;

use App\Models\Project;
use App\Models\User;
use Database\Seeders\DemoSeeder;
use Illuminate\Foundation\Testing\RefreshDatabase;
use RuntimeException;
use Tests\TestCase;

class PublicDemoTest extends TestCase
{
    use RefreshDatabase;

    public function test_demo_seed_allows_real_login_and_board_access(): void
    {
        config(['demo.enabled' => true]);
        $this->seed(DemoSeeder::class);
        $this->withHeader('Origin', 'http://localhost:3000')->postJson('/api/auth/login', [
            'email' => 'demo@example.com', 'password' => 'TicketDemo2026!',
        ])->assertOk()->assertJsonPath('user.role', 'user');
        $this->getJson('/api/projects')->assertOk();
        $this->assertDatabaseCount('tickets', 5);
        $this->assertDatabaseHas('project_members', ['role' => 'leader', 'permission' => 'write']);
    }

    public function test_demo_blocks_account_creation_mail_and_oauth(): void
    {
        config(['demo.enabled' => true]);
        foreach (['register', 'forgot-password', 'reset-password', 'email/verification-notification'] as $path) {
            $this->postJson('/api/auth/'.$path, [])->assertForbidden();
        }
        foreach (['google/redirect', 'google/callback', 'line/redirect', 'line/callback', 'email/verify/1/hash'] as $path) {
            $this->getJson('/api/auth/'.$path)->assertForbidden();
        }
        $this->assertDatabaseCount('users', 0);
    }

    public function test_demo_does_not_bypass_authentication(): void
    {
        config(['demo.enabled' => true]);
        $this->getJson('/api/projects')->assertUnauthorized();
    }

    public function test_normal_mode_keeps_registration_validation(): void
    {
        config(['demo.enabled' => false]);
        $this->postJson('/api/auth/register', [])->assertUnprocessable();
    }

    public function test_seed_refuses_non_demo_environment(): void
    {
        config(['demo.enabled' => false]);
        $this->expectException(RuntimeException::class);
        $this->seed(DemoSeeder::class);
    }

    public function test_seed_refuses_existing_users(): void
    {
        config(['demo.enabled' => true]);
        User::factory()->create();
        $this->expectException(RuntimeException::class);
        $this->seed(DemoSeeder::class);
    }

    public function test_seed_refuses_existing_project_data(): void
    {
        config(['demo.enabled' => true]);
        Project::factory()->create();
        $this->expectException(RuntimeException::class);
        $this->seed(DemoSeeder::class);
    }
}
