<?php

namespace Tests\Feature;

use App\Models\Post;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class PostApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_post_can_be_created(): void
    {
        $response = $this->postJson('/api/posts', [
            'content' => '最初の投稿です。',
            'image_url' => null,
        ]);

        $response->assertCreated();

        $response->assertJson([
            'message' => 'Post created',
            'data' => [
                'content' => '最初の投稿です。',
                'image_url' => null,
            ],
        ]);

        $this->assertDatabaseHas('posts', [
            'content' => '最初の投稿です。',
            'image_url' => null,
        ]);
    }

    public function test_post_can_be_shown(): void
    {
        $post = Post::create([
            'content' => '詳細確認用の投稿です。',
            'image_url' => null,
        ]);

        $response = $this->getJson("/api/posts/{$post->id}");

        $response->assertOk();

        $response->assertJson([
            'message' => 'Post detail',
            'data' => [
                'id' => $post->id,
                'content' => '詳細確認用の投稿です。',
                'image_url' => null,
            ],
        ]);
    }

    public function test_post_can_be_updated(): void
    {
        $post = Post::create([
            'content' => '更新前の投稿です。',
            'image_url' => null,
        ]);

        $response = $this->putJson("/api/posts/{$post->id}", [
            'content' => '更新後の投稿です。',
            'image_url' => 'https://example.com/image.jpg',
        ]);

        $response->assertOk();

        $response->assertJson([
            'message' => 'Post updated',
            'data' => [
                'id' => $post->id,
                'content' => '更新後の投稿です。',
                'image_url' => 'https://example.com/image.jpg',
            ],
        ]);

        $this->assertDatabaseHas('posts', [
            'id' => $post->id,
            'content' => '更新後の投稿です。',
            'image_url' => 'https://example.com/image.jpg',
        ]);
    }

    public function test_post_can_be_deleted(): void
    {
        $post = Post::create([
            'content' => '削除対象の投稿です。',
            'image_url' => null,
        ]);

        $response = $this->deleteJson("/api/posts/{$post->id}");

        $response->assertOk();

        $response->assertJson([
            'message' => 'Post deleted',
        ]);

        $this->assertDatabaseMissing('posts', [
            'id' => $post->id,
        ]);
    }
}