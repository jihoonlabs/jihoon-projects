<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('ticket_audit_events', function (Blueprint $table) {
            $table->id();
            // No foreign keys: the evidence must outlive ticket, project and user deletion.
            $table->unsignedBigInteger('project_id');
            $table->string('project_key', 3);
            $table->unsignedBigInteger('ticket_id');
            $table->string('issue_key');
            $table->unsignedBigInteger('actor_id');
            $table->string('actor_name');
            $table->string('action', 32);
            $table->json('snapshot');
            $table->timestamp('created_at')->useCurrent();

            $table->index(['project_key', 'created_at']);
            $table->index(['ticket_id', 'created_at']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('ticket_audit_events');
    }
};
