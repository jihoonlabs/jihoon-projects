<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('tickets', function (Blueprint $table) {
            $table->unsignedInteger('position')->default(0)->after('status');
        });

        Schema::table('projects', function (Blueprint $table) {
            $table->unsignedBigInteger('board_version')->default(0)->after('name');
        });

        $projectIds = DB::table('tickets')->distinct()->pluck('project_id');
        foreach ($projectIds as $projectId) {
            $statuses = DB::table('tickets')
                ->where('project_id', $projectId)
                ->distinct()
                ->pluck('status');

            foreach ($statuses as $status) {
                DB::table('tickets')
                    ->where('project_id', $projectId)
                    ->where('status', $status)
                    ->orderBy('id')
                    ->pluck('id')
                    ->each(fn ($id, $position) => DB::table('tickets')
                        ->where('id', $id)
                        ->update(['position' => $position]));
            }
        }
    }

    public function down(): void
    {
        Schema::table('projects', function (Blueprint $table) {
            $table->dropColumn('board_version');
        });

        Schema::table('tickets', function (Blueprint $table) {
            $table->dropColumn('position');
        });
    }
};
