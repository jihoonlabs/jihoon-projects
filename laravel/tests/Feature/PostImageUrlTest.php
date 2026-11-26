<?php

namespace Tests\Feature;

use App\Models\Post;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\TestCase;

class PostImageUrlTest extends TestCase
{
    use RefreshDatabase;

    public function test_http_url_can_be_saved_when_creating_a_post(): void
    {
        $this->actingAs(User::factory()->create())
            ->postJson('/api/posts', [
                'content' => '画像付きの投稿',
                'image_url' => 'http://example.com/image.jpg',
            ])
            ->assertCreated()
            ->assertJsonPath('data.image_url', 'http://example.com/image.jpg');

        $this->assertDatabaseHas('posts', ['image_url' => 'http://example.com/image.jpg']);
    }

    #[DataProvider('invalidImageUrls')]
    public function test_invalid_image_url_is_rejected_when_creating_or_updating_a_post(string $imageUrl): void
    {
        $post = Post::create([
            'content' => '変更前の投稿',
            'image_url' => 'https://example.com/original.jpg',
        ]);
        $data = ['content' => '変更後の投稿', 'image_url' => $imageUrl];

        $this->actingAs(User::factory()->create())
            ->postJson('/api/posts', $data)
            ->assertUnprocessable()
            ->assertJsonValidationErrors('image_url');

        $this->putJson("/api/posts/{$post->id}", $data)
            ->assertUnprocessable()
            ->assertJsonValidationErrors('image_url');

        $this->assertDatabaseCount('posts', 1);
        $this->assertDatabaseHas('posts', [
            'id' => $post->id,
            'content' => '変更前の投稿',
            'image_url' => 'https://example.com/original.jpg',
        ]);
    }

    public static function invalidImageUrls(): array
    {
        return [
            '不正なURL' => ['not a URL'],
            '相対URL' => ['/image.jpg'],
            '許可されていないスキーム' => ['ftp://example.com/image.jpg'],
            '保存上限を超えるURL' => ['https://example.com/'.str_repeat('a', 255)],
        ];
    }
}
