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
            $table->foreignId('project_id')->nullable()->after('id')->constrained()->restrictOnDelete();
        });

        $now = now();
        $projectId = DB::table('projects')->insertGetId([
            'name' => 'General',
            'created_at' => $now,
            'updated_at' => $now,
        ]);

        DB::table('tickets')
            ->whereNull('project_id')
            ->update(['project_id' => $projectId]);

        $members = DB::table('users')
            ->where('status', 'active')
            ->select('id')
            ->get()
            ->map(fn ($user) => [
                'project_id' => $projectId,
                'user_id' => $user->id,
                'role' => 'member',
                'permission' => 'write',
                'created_at' => $now,
                'updated_at' => $now,
            ])
            ->all();

        if ($members !== []) {
            DB::table('project_members')->insert($members);
        }

        Schema::table('tickets', function (Blueprint $table) {
            $table->foreignId('project_id')->nullable(false)->change();
        });
    }

    public function down(): void
    {
        Schema::table('tickets', function (Blueprint $table) {
            $table->dropConstrainedForeignId('project_id');
        });
    }
};
