<?php

namespace Tests\Feature;

/*
| Notice 모델: DB에 직접 데이터 생성할 때 사용
| RefreshDatabase: 테스트마다 DB를 초기화해서 깨끗한 상태 유지
| TestCase: Laravel 테스트 기본 클래스
*/
use App\Models\Notice;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class NoticeApiTest extends TestCase
{
    use RefreshDatabase;


    /*
    |
    | 1. no title POST 
    | 2. 422 status 
    | 3. title validation error 
    */
    public function test_title_is_required_when_creating_notice(): void
    {
        $response = $this->postJson('/api/notices', [
            'content' => 'title nothing', // no title
        ]);

        $response->assertStatus(422); // error
        $response->assertJsonValidationErrors(['title']);
    }

    /*
    | 1. title + content POST 
    | 2. 201 Created
    | 3. JSON 
    | 4. DB check
    */

    public function test_notice_can_be_created(): void
    {
        $response = $this->postJson('/api/notices', [
            'title' => '1st',
            'content' => 'test',
        ]);

        $response->assertStatus(201);
        $response->assertJson([
            'title' => '1st',
            'content' => 'test',
        ]);

        // checked DB 
        $this->assertDatabaseHas('notices', [
            'title' => '1st',
            'content' => 'test',
        ]);
    }

    /*
    | 1. create
    | 2. GET list
    | 3. 200 OK
    | 4. checked update Data
    */
    public function test_notice_list_can_be_fetched(): void
    {
        Notice::create([
            'title' => 'test 1',
            'content' => 'text 1',
        ]);

        $response = $this->getJson('/api/notices');

        $response->assertStatus(200);
        $response->assertJsonFragment([
            'title' => 'test 1',
            'content' => 'text 1',
        ]);
    }
}