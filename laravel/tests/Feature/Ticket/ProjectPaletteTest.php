<?php

namespace Tests\Feature\Ticket;

use App\Models\Project;
use App\Models\User;
use App\Support\ProjectPalette;
use Illuminate\Database\QueryException;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
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
        foreach ($palette as $hex) {
            $rgb = array_map('hexdec', str_split(substr($hex, 1), 2));
            $this->assertGreaterThanOrEqual(217, min($rgb));
            $channels = array_map(static fn ($v) => ($v / 255 <= 0.04045) ? $v / 255 / 12.92 : (($v / 255 + 0.055) / 1.055) ** 2.4, $rgb);
            $this->assertGreaterThan(7, (0.2126 * $channels[0] + 0.7152 * $channels[1] + 0.0722 * $channels[2] + 0.05) / 0.05);
            // Red/magenta would require red to dominate both green and blue.
            $this->assertFalse($rgb[0] > $rgb[1] && $rgb[2] > $rgb[1]);
        }
    }

    public function test_exhaustion_refuses_to_reuse_a_color(): void
    {
        foreach (array_slice(ProjectPalette::colors(), Project::count()) as $index => $color) {
            Project::create(['name' => 'Palette '.$index]);
        }
        $user = User::factory()->create(['status' => 'active']);
        $count = Project::count();
        $this->actingAs($user)->postJson('/api/projects', ['name' => 'Overflow'])->assertStatus(503);
        $this->assertSame($count, Project::count());
    }
}
