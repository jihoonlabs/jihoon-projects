<?php

namespace Tests\Feature\Ticket;

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;
use Tests\TestCase;

class ProjectTicketKeyMigrationTest extends TestCase
{
    private string $connection = 'project_ticket_key_migration_test';

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
            $table->unsignedBigInteger('board_version')->default(0);
            $table->timestamps();
        });
        Schema::create('tickets', function ($table) {
            $table->id();
            $table->foreignId('project_id');
            $table->string('issue_key')->nullable()->unique();
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

    public function test_existing_projects_and_tickets_receive_project_scoped_keys(): void
    {
        $firstProject = DB::table('projects')->insertGetId(['name' => 'First']);
        $secondProject = DB::table('projects')->insertGetId(['name' => 'Second']);

        DB::table('tickets')->insert([
            ['project_id' => $firstProject, 'issue_key' => 'TICK-10', 'title' => 'A'],
            ['project_id' => $firstProject, 'issue_key' => 'TICK-20', 'title' => 'B'],
            ['project_id' => $secondProject, 'issue_key' => 'TICK-30', 'title' => 'C'],
        ]);

        /** @var Migration $migration */
        $migration = require database_path('migrations/2026_10_07_000001_add_project_ticket_keys.php');
        $migration->up();

        $first = DB::table('projects')->find($firstProject);
        $second = DB::table('projects')->find($secondProject);

        $this->assertMatchesRegularExpression('/^[A-Z]{3}$/', $first->project_key);
        $this->assertMatchesRegularExpression('/^[A-Z]{3}$/', $second->project_key);
        $this->assertNotSame($first->project_key, $second->project_key);
        $this->assertSame(3, (int) $first->next_ticket_number);
        $this->assertSame(2, (int) $second->next_ticket_number);

        $this->assertSame(
            [$first->project_key.'-01', $first->project_key.'-02'],
            DB::table('tickets')->where('project_id', $firstProject)->orderBy('id')->pluck('issue_key')->all()
        );
        $this->assertSame(
            [$second->project_key.'-01'],
            DB::table('tickets')->where('project_id', $secondProject)->pluck('issue_key')->all()
        );
    }
}
