<?php

use App\Support\ProjectPalette;
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        $ids = DB::table('projects')->orderBy('id')->pluck('id');
        $palette = ProjectPalette::colors();
        if ($ids->count() > count($palette)) {
            throw new RuntimeException('Project count exceeds the distinct pale palette capacity.');
        }
        Schema::table('projects', function (Blueprint $table) {
            $table->string('color', 7)->nullable()->unique();
        });
        foreach ($ids as $index => $id) {
            DB::table('projects')->where('id', $id)->update(['color' => $palette[$index]]);
        }
        Schema::table('projects', function (Blueprint $table) {
            $table->string('color', 7)->nullable(false)->change();
        });
    }

    public function down(): void
    {
        Schema::table('projects', function (Blueprint $table) {
            $table->dropUnique(['color']);
            $table->dropColumn('color');
        });
    }
};
