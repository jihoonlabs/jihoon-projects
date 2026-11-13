<?php

namespace Tests\Feature;

use App\Models\Notice;
use App\Models\Post;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\TestCase;

class ContentAccessTest extends TestCase
{
    use RefreshDatabase;

    public static function contentTypes(): array
    {
        return [
            '投稿' => ['posts', Post::class, ['content' => '既存の投稿'], ['content' => '新しい投稿']],
            'お知らせ' => ['notices', Notice::class, ['title' => '既存のお知らせ'], ['title' => '新しいお知らせ']],
        ];
    }

    #[DataProvider('contentTypes')]
    public function test_guests_can_read_content_but_cannot_change_it(
        string $resource,
        string $model,
        array $original,
        array $change,
    ): void {
        $item = $model::create($original);
        $collection = '/api/'.$resource;
        $detail = $collection.'/'.$item->id;

        $this->getJson($collection)->assertOk()->assertJsonPath('data.0.id', $item->id);
        $this->getJson($detail)->assertOk()->assertJsonPath('data.id', $item->id);

        $this->postJson($collection, $change)->assertUnauthorized();
        $this->putJson($detail, $change)->assertUnauthorized();
        $this->deleteJson($detail)->assertUnauthorized();

        $this->assertDatabaseCount($resource, 1);
        $this->assertDatabaseHas($resource, ['id' => $item->id] + $original);
    }

    #[DataProvider('contentTypes')]
    public function test_active_users_can_change_content_in_normal_mode(
        string $resource,
        string $model,
        array $original,
        array $change,
    ): void {
        config(['demo.enabled' => false]);
        $this->actingAs(User::factory()->create(['status' => 'active']));
        $collection = '/api/'.$resource;

        $this->postJson($collection, $original)->assertCreated();
        $item = $model::sole();
        $detail = $collection.'/'.$item->id;
        $this->assertDatabaseHas($resource, ['id' => $item->id] + $original);

        $this->putJson($detail, $change)->assertOk();
        $this->assertDatabaseHas($resource, ['id' => $item->id] + $change);

        $this->deleteJson($detail)->assertOk();
        $this->assertDatabaseMissing($resource, ['id' => $item->id]);
    }

    #[DataProvider('contentTypes')]
    public function test_suspended_users_cannot_change_content(
        string $resource,
        string $model,
        array $original,
        array $change,
    ): void {
        config(['demo.enabled' => false]);
        $item = $model::create($original);
        $this->actingAs(User::factory()->create(['status' => 'suspended']));

        $this->putJson('/api/'.$resource.'/'.$item->id, $change)->assertForbidden();
        $this->assertDatabaseHas($resource, ['id' => $item->id] + $original);
    }

    #[DataProvider('contentTypes')]
    public function test_demo_allows_reading_but_disallows_changes(
        string $resource,
        string $model,
        array $original,
        array $change,
    ): void {
        config(['demo.enabled' => true]);
        $this->actingAs(User::factory()->create(['status' => 'active', 'role' => 'admin']));
        $item = $model::create($original);
        $collection = '/api/'.$resource;
        $detail = $collection.'/'.$item->id;

        $this->getJson($collection)->assertOk();
        $this->getJson($detail)->assertOk();

        $this->postJson($collection, $change)->assertForbidden();
        $this->putJson($detail, $change)->assertForbidden();
        $this->deleteJson($detail)->assertForbidden();

        $this->assertDatabaseCount($resource, 1);
        $this->assertDatabaseHas($resource, ['id' => $item->id] + $original);
    }
}
