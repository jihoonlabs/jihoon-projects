<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\User;
use App\Support\ProjectPalette;
use Illuminate\Database\QueryException;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Mockery;
use Tests\TestCase;

class ProjectPaletteTest extends TestCase
{
    use RefreshDatabase;

    public function test_create_rename_and_other_member_keep_distinct_stored_colors(): void
    {
        $admin = User::factory()->create(['role' => 'admin', 'status' => 'active']);
        $other = User::factory()->create(['status' => 'active']);
        $first = $this->actingAs($admin)->postJson('/api/projects', ['name' => 'One', 'color' => '#000000'])->assertCreated()->json('data');
        $second = $this->postJson('/api/projects', ['name' => 'Two'])->assertCreated()->json('data');
        $this->assertNotSame($first['color'], $second['color']);
        $this->assertContains($first['color'], ProjectPalette::colors());
        $this->assertDatabaseHas('projects', ['id' => $first['id'], 'color' => $first['color']]);
        $this->patchJson('/api/projects/'.$first['id'], ['name' => 'Renamed', 'color' => '#000000'])->assertOk()->assertJsonPath('data.color', $first['color']);
        Project::findOrFail($first['id'])->members()->attach($other->id, ['role' => 'member', 'permission' => 'read']);
        $this->actingAs($other)->getJson('/api/projects/'.$first['id'])->assertOk()->assertJsonPath('data.color', $first['color']);
    }

    public function test_database_rejects_duplicate_colors(): void
    {
        $first = Project::create(['name' => 'First']);
        $second = Project::create(['name' => 'Second']);
        $this->expectException(QueryException::class);
        DB::table('projects')->where('id', $second->id)->update(['color' => $first->color]);
    }

    public function test_palette_is_unique_pale_and_readable_with_black_text(): void
    {
        $palette = ProjectPalette::colors();
        $this->assertSame(count($palette), count(array_unique($palette)));
        $this->assertPaletteSampleIsPaleAndReadable($palette[0]);
        $this->assertPaletteSampleIsPaleAndReadable($palette[1]);
        $this->assertPaletteSampleIsPaleAndReadable($palette[8]);
        $this->assertPaletteSampleIsPaleAndReadable($palette[count($palette) - 1]);
    }

    private function assertPaletteSampleIsPaleAndReadable(string $hex): void
    {
        $red = hexdec(substr($hex, 1, 2));
        $green = hexdec(substr($hex, 3, 2));
        $blue = hexdec(substr($hex, 5, 2));
        $this->assertGreaterThanOrEqual(217, min($red, $green, $blue));

        $linear = static fn (int $channel): float => $channel / 255 <= 0.04045
            ? $channel / 255 / 12.92
            : (($channel / 255 + 0.055) / 1.055) ** 2.4;
        $luminance = 0.2126 * $linear($red)
            + 0.7152 * $linear($green)
            + 0.0722 * $linear($blue);
        $this->assertGreaterThan(7, ($luminance + 0.05) / 0.05);
        $this->assertFalse($red > $green && $blue > $green);
    }

    public function test_exhaustion_refuses_to_reuse_a_color(): void
    {
        $query = Mockery::mock();
        $query->shouldReceive('pluck')
            ->once()
            ->with('color')
            ->andReturn(collect(ProjectPalette::colors()));
        DB::shouldReceive('table')->once()->with('projects')->andReturn($query);

        $this->expectException(\Symfony\Component\HttpKernel\Exception\HttpException::class);
        $this->expectExceptionCode(503);

        ProjectPalette::next();
    }
}
