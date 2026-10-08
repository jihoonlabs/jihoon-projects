<?php

namespace Tests\Feature\Ticket;

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;
use Tests\TestCase;

class ProjectLifecycleAuditMigrationTest extends TestCase
{
    private string $connection = 'project_lifecycle_migration_test';

    protected function setUp(): void
    {
        parent::setUp();

        config([
            "database.connections.{$this->connection}" => array_merge(
                config('database.connections.sqlite'),
                ['database' => ':memory:']
            ),
        ]);
        DB::purge($this->connection);
        DB::setDefaultConnection($this->connection);

        Schema::create('projects', function ($table) {
            $table->id();
            $table->string('name');
            $table->string('project_key', 3)->unique();
            $table->timestamps();
        });
        DB::table('projects')->insert([
            'name' => 'Legacy Project',
            'project_key' => 'OLD',
            'created_at' => now(),
            'updated_at' => now(),
        ]);
    }

    protected function tearDown(): void
    {
        DB::setDefaultConnection(config('database.default'));
        DB::purge($this->connection);

        parent::tearDown();
    }

    public function test_lifecycle_audit_and_creator_migrations_preserve_legacy_projects_in_order(): void
    {
        $migrations = [
            '2026_10_08_000001_add_archived_at_to_projects_table.php',
            '2026_10_08_000003_create_project_audit_events_table.php',
            '2026_10_08_000004_add_created_by_to_projects_table.php',
        ];

        foreach ($migrations as $file) {
            /** @var Migration $migration */
            $migration = require database_path("migrations/{$file}");
            $migration->up();
        }

        $legacy = DB::table('projects')->where('project_key', 'OLD')->first();
        $this->assertNotNull($legacy);
        $this->assertNull($legacy->archived_at);
        $this->assertNull($legacy->created_by);
        $this->assertSame(1, DB::table('projects')->count());
        $this->assertTrue(Schema::hasTable('project_audit_events'));
        $this->assertSame([], DB::select("PRAGMA foreign_key_list('project_audit_events')"));
    }
}
