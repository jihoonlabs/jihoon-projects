<?php

namespace App\Http\Resources\Attendance;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class AttendanceRecordResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        $breaks = $this->breaks;
        $breakSeconds = (int) $breaks->sum(
            fn ($break) => $break->ended_at === null
                ? 0
                : max(0, $break->started_at->diffInSeconds($break->ended_at)),
        );
        $durationSeconds = null;

        if ($this->clock_out_at !== null) {
            $grossSeconds = max(0, $this->clock_in_at->diffInSeconds($this->clock_out_at));
            $durationSeconds = max(0, $grossSeconds - $breakSeconds);
        }

        return [
            'id' => $this->id,
            'work_date' => $this->work_date->toDateString(),
            'clock_in_at' => $this->clock_in_at->toImmutable()->utc()->toIso8601String(),
            'clock_out_at' => $this->clock_out_at?->toImmutable()->utc()->toIso8601String(),
            'breaks' => $breaks->map(fn ($break) => [
                'id' => $break->id,
                'started_at' => $break->started_at->toImmutable()->utc()->toIso8601String(),
                'ended_at' => $break->ended_at?->toImmutable()->utc()->toIso8601String(),
            ])->values(),
            'break_duration_seconds' => $breakSeconds,
            'break_duration_minutes' => intdiv($breakSeconds, 60),
            'duration_seconds' => $durationSeconds,
            'duration_minutes' => $durationSeconds === null ? null : intdiv($durationSeconds, 60),
        ];
    }
}
