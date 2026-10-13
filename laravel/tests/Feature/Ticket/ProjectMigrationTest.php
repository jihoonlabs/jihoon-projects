<?php

namespace Tests\Feature\Ticket;

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;
use Tests\TestCase;

class ProjectMigrationTest extends TestCase
{
    private string $connection = 'project_migration_test';

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

        Schema::create('users', function ($table) {
            $table->id();
            $table->string('name');
            $table->string('email')->unique();
            $table->string('status')->default('active');
        });
        Schema::create('projects', function ($table) {
            $table->id();
            $table->string('name');
            $table->timestamps();
        });
        Schema::create('project_members', function ($table) {
            $table->id();
            $table->foreignId('project_id')->constrained()->cascadeOnDelete();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('role')->default('member');
            $table->string('permission')->default('read');
            $table->timestamps();
            $table->unique(['project_id', 'user_id']);
        });
        Schema::create('tickets', function ($table) {
            $table->id();
            $table->string('title');
            $table->timestamps();
        });
    }

    protected function tearDown(): void
    {
        DB::setDefaultConnection(config('database.default'));
        DB::purge($this->connection);

        parent::tearDown();
    }

    public function test_existing_tickets_are_preserved_in_general_and_active_users_receive_write_access(): void
    {
        $activeId = DB::table('users')->insertGetId([
            'name' => 'Active Member',
            'email' => 'active@example.test',
            'status' => 'active',
        ]);
        DB::table('users')->insert([
            'name' => 'Inactive Member',
            'email' => 'inactive@example.test',
            'status' => 'suspended',
        ]);
        $ticketId = DB::table('tickets')->insertGetId([
            'title' => 'Legacy ticket',
            'created_at' => now(),
            'updated_at' => now(),
        ]);

        /** @var Migration $migration */
        $migration = require database_path('migrations/2026_10_01_000004_add_project_id_to_tickets_table.php');
        $migration->up();

        $project = DB::table('projects')->where('name', 'General')->first();
        $this->assertNotNull($project);
        $this->assertDatabaseHas('tickets', [
            'id' => $ticketId,
            'project_id' => $project->id,
            'title' => 'Legacy ticket',
        ]);
        $this->assertDatabaseHas('project_members', [
            'project_id' => $project->id,
            'user_id' => $activeId,
            'role' => 'member',
            'permission' => 'write',
        ]);
        $this->assertDatabaseCount('project_members', 1);
        $columns = array_values(array_filter(
            DB::select("PRAGMA table_info('tickets')"),
            fn ($column) => $column->name === 'project_id'
        ));
        $this->assertSame(1, $columns[0]->notnull);
    }
}
