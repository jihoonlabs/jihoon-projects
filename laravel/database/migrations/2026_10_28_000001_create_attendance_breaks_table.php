<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('attendance_breaks', function (Blueprint $table) {
            $table->id();
            $table->foreignId('attendance_record_id')->constrained()->cascadeOnDelete();
            $table->timestamp('started_at');
            $table->timestamp('ended_at')->nullable();
            $table->timestamps();

            $table->index(['attendance_record_id', 'ended_at']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('attendance_breaks');
    }
};
