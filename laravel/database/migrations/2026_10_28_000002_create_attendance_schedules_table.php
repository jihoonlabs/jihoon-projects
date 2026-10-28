<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('attendance_schedules', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->date('effective_from');
            $table->json('weekdays');
            $table->time('start_time');
            $table->time('end_time');
            $table->unsignedSmallInteger('planned_break_minutes')->default(0);
            $table->timestamps();
            $table->unique(['user_id', 'effective_from']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('attendance_schedules');
    }
};
