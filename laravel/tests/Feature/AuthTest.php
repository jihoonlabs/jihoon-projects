<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Tests\TestCase;

class AuthTest extends TestCase
{
    use RefreshDatabase; // 테스트 실행 후 DB를 깨끗하게 리셋합니다.

    /**
     * Test 1: 올바른 계정 정보 입력 시 Bearer 토큰 발급 테스트
     */
    public function test_user_can_login_with_correct_credentials(): void
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123'),
        ]);

        $response = $this->postJson('/api/auth/login', [
            'email' => 'test@example.com',
            'password' => 'password123',
        ]);

        $response->assertStatus(200)
                 ->assertJsonStructure([
                     'message',
                     'access_token',
                     'token_type',
                     'user' => ['id', 'name', 'email'],
                 ]);
    }

    /**
     * Test 2: 잘못된 비밀번호 입력 시 로그인 실패 테스트
     */
    public function test_user_cannot_login_with_incorrect_password(): void
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123'),
        ]);

        $response = $this->postJson('/api/auth/login', [
            'email' => 'test@example.com',
            'password' => 'wrong-password',
        ]);

        $response->assertStatus(422)
                 ->assertJsonValidationErrors(['email']);
    }

    /**
     * Test 3: Sanctum 토큰으로 로그인 유저 정보 조회 (/api/auth/me)
     */
    public function test_authenticated_user_can_get_profile(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user, 'sanctum')
                         ->getJson('/api/auth/me');

        $response->assertStatus(200)
                 ->assertJson([
                     'id' => $user->id,
                     'email' => $user->email,
                 ]);
    }

    /**
     * Test 4: 로그아웃 시 토큰 폐기 테스트
     */
    public function test_user_can_logout(): void
    {
        $user = User::factory()->create();
        $token = $user->createToken('test_token')->plainTextToken;

        $response = $this->withHeader('Authorization', 'Bearer ' . $token)
                         ->postJson('/api/auth/logout');

        $response->assertStatus(200)
                 ->assertJson(['message' => 'ログアウトしました。']);

        $this->assertCount(0, $user->tokens);
    }
}