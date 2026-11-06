<?php

namespace App\Http\Resources\Attendance;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class AttendanceRecordResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        $durationMinutes = null;

        if ($this->clock_out_at !== null) {
            $seconds = max(0, $this->clock_in_at->diffInSeconds($this->clock_out_at));
            $durationMinutes = intdiv((int) $seconds, 60);
        }

        return [
            'id' => $this->id,
            'work_date' => $this->work_date->toDateString(),
            'clock_in_at' => $this->clock_in_at->toImmutable()->utc()->toIso8601String(),
            'clock_out_at' => $this->clock_out_at?->toImmutable()->utc()->toIso8601String(),
            'duration_minutes' => $durationMinutes,
        ];
    }
}
