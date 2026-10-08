<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('project_audit_events', function (Blueprint $table) {
            $table->id();
            // No FK: historical project identity must survive live row deletion.
            $table->unsignedBigInteger('project_id');
            $table->string('project_key', 3);
            $table->unsignedBigInteger('actor_id');
            $table->string('actor_name');
            $table->string('action', 32);
            $table->json('snapshot');
            $table->timestamp('created_at')->useCurrent();
            $table->index(['project_key', 'created_at']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('project_audit_events');
    }
};
