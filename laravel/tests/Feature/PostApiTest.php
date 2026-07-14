<?php

namespace Tests\Feature;

use App\Models\Post;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class PostApiTest extends TestCase
{
    use RefreshDatabase;

    /**
     * 게시글을 생성할 수 있다.
     */
    public function test_post_can_be_created(): void
    {
        // 실제 서버를 띄우지 않고 Laravel 내부에서 POST 요청을 보냄
        $response = $this->postJson('/api/posts', [
            'content' => '첫 번째 게시글입니다.',
            'image_url' => null,
        ]);

        // HTTP 상태 코드가 201 Created인지 확인
        $response->assertCreated();

        // 응답 JSON에 원하는 데이터가 포함됐는지 확인
        $response->assertJson([
            'message' => 'Post created',
            'data' => [
                'content' => '첫 번째 게시글입니다.',
                'image_url' => null,
            ],
        ]);

        // 실제 테스트 DB에도 데이터가 저장됐는지 확인
        $this->assertDatabaseHas('posts', [
            'content' => '첫 번째 게시글입니다.',
            'image_url' => null,
        ]);
    }
    
    /**
     * 게시글 하나를 조회할 수 있다.
     */
    public function test_post_can_be_shown(): void
    {
        $post = Post::create([
            'content' => '상세 조회용 게시글입니다.',
            'image_url' => null,
        ]);

        $response = $this->getJson("/api/posts/{$post->id}");

        $response->assertOk();

        $response->assertJson([
            'message' => 'Post detail',
            'data' => [
                'id' => $post->id,
                'content' => '상세 조회용 게시글입니다.',
                'image_url' => null,
            ],
        ]);
    }

    /**
     * 게시글을 수정할 수 있다.
     */
    public function test_post_can_be_updated(): void
    {
        // 수정할 게시글 생성
        $post = Post::create([
            'content' => '수정 전 게시글입니다.',
            'image_url' => null,
        ]);

        // 해당 게시글 수정 요청
        $response = $this->putJson("/api/posts/{$post->id}", [
            'content' => '수정된 게시글입니다.',
            'image_url' => 'https://example.com/image.jpg',
        ]);

        // HTTP 200 OK 확인
        $response->assertOk();

        // JSON 응답 확인
        $response->assertJson([
            'message' => 'Post updated',
            'data' => [
                'id' => $post->id,
                'content' => '수정된 게시글입니다.',
                'image_url' => 'https://example.com/image.jpg',
            ],
        ]);

        // 테스트 DB의 실제 변경 내용 확인
        $this->assertDatabaseHas('posts', [
            'id' => $post->id,
            'content' => '수정된 게시글입니다.',
            'image_url' => 'https://example.com/image.jpg',
        ]);
    }
    
    /**
     * 게시글을 삭제할 수 있다.
     */
    public function test_post_can_be_deleted(): void
    {
        // 삭제할 게시글 생성
        $post = Post::create([
            'content' => '삭제할 게시글입니다.',
            'image_url' => null,
        ]);

        // 해당 게시글 삭제 요청
        $response = $this->deleteJson("/api/posts/{$post->id}");

        // HTTP 200 OK 확인
        $response->assertOk();

        // JSON 응답 확인
        $response->assertJson([
            'message' => 'Post deleted',
        ]);

        // 테스트 DB에서 실제로 삭제됐는지 확인
        $this->assertDatabaseMissing('posts', [
            'id' => $post->id,
        ]);
    }
}