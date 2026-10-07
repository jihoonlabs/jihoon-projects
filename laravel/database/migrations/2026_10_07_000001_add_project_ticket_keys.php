<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('projects', function (Blueprint $table) {
            $table->string('project_key', 3)->nullable()->unique()->after('name');
            $table->unsignedBigInteger('next_ticket_number')->default(1)->after('project_key');
        });

        $usedKeys = [];
        $projects = DB::table('projects')->orderBy('id')->get(['id']);

        foreach ($projects as $project) {
            do {
                $key = '';
                for ($i = 0; $i < 3; $i++) {
                    $key .= chr(random_int(65, 90));
                }
            } while (isset($usedKeys[$key]));

            $usedKeys[$key] = true;

            $tickets = DB::table('tickets')
                ->where('project_id', $project->id)
                ->orderBy('id')
                ->pluck('id');

            foreach ($tickets as $index => $ticketId) {
                DB::table('tickets')
                    ->where('id', $ticketId)
                    ->update(['issue_key' => sprintf('%s-%02d', $key, $index + 1)]);
            }

            DB::table('projects')
                ->where('id', $project->id)
                ->update([
                    'project_key' => $key,
                    'next_ticket_number' => $tickets->count() + 1,
                ]);
        }

        Schema::table('projects', function (Blueprint $table) {
            $table->string('project_key', 3)->nullable(false)->change();
        });
    }

    public function down(): void
    {
        Schema::table('projects', function (Blueprint $table) {
            $table->dropUnique(['project_key']);
            $table->dropColumn(['project_key', 'next_ticket_number']);
        });
    }
};
