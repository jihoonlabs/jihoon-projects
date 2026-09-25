<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('tickets', function (Blueprint $table) {
            $table->id();
            $table->string('issue_key')->unique();
            $table->string('title');
            $table->text('description')->nullable();

            $table->enum('status', ['BACKLOG', 'TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE'])
                ->default('TODO');

            $table->enum('priority', ['HIGHEST', 'HIGH', 'MEDIUM', 'LOW', 'LOWEST'])
                ->default('MEDIUM');

            $table->foreignId('assignee_id')
                ->nullable()
                ->constrained('users')
                ->nullOnDelete();

            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('tickets');
    }
};
