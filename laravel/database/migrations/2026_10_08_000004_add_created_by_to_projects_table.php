<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('projects', function (Blueprint $table) {
            // Nullable for legacy projects; do not infer creator from the current leader.
            $table->unsignedBigInteger('created_by')->nullable()->index();
        });
    }

    public function down(): void
    {
        Schema::table('projects', function (Blueprint $table) {
            $table->dropIndex(['created_by']);
            $table->dropColumn('created_by');
        });
    }
};
