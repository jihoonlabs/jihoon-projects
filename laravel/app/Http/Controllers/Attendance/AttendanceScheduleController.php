<?php

namespace App\Http\Controllers\Attendance;

use App\Http\Controllers\Controller;
use App\Models\AttendanceSchedule;
use App\Models\User;
use Carbon\CarbonImmutable;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
use Illuminate\Validation\ValidationException;

class AttendanceScheduleController extends Controller
{
    private const TIMEZONE = 'Asia/Tokyo';

    public function users(Request $request): JsonResponse
    {
        $this->authorizeAdmin($request);

        return response()->json([
            'data' => User::query()
                ->where('role', 'user')
                ->where('status', 'active')
                ->orderBy('name')
                ->orderBy('id')
                ->get(['id', 'name', 'email']),
        ]);
    }

    public function show(Request $request): JsonResponse
    {
        $targetUser = $this->targetEmployee($request);
        $today = CarbonImmutable::now(self::TIMEZONE)->toDateString();
        $schedules = $targetUser->attendanceSchedules();

        $current = (clone $schedules)
            ->whereDate('effective_from', '<=', $today)
            ->orderByDesc('effective_from')
            ->first();

        $upcoming = $schedules
            ->whereDate('effective_from', '>', $today)
            ->orderBy('effective_from')
            ->first();

        return response()->json([
            'data' => [
                'date' => $today,
                'timezone' => self::TIMEZONE,
                'current' => $current === null ? null : $this->serialize($current),
                'upcoming' => $upcoming === null ? null : $this->serialize($upcoming),
            ],
        ]);
    }

    public function store(Request $request): JsonResponse
    {
        $this->authorizeAdmin($request);

        $today = CarbonImmutable::now(self::TIMEZONE)->toDateString();
        $validated = $request->validate([
            'user_id' => [
                'required',
                'integer',
                Rule::exists('users', 'id')
                    ->where('role', 'user')
                    ->where('status', 'active'),
            ],
            'effective_from' => ['required', 'date_format:Y-m-d', 'after_or_equal:'.$today],
            'weekdays' => ['required', 'array', 'min:1', 'max:7'],
            'weekdays.*' => ['required', 'integer', 'between:1,7', 'distinct'],
            'start_time' => ['required', 'date_format:H:i'],
            'end_time' => ['required', 'date_format:H:i'],
            'planned_break_minutes' => ['required', 'integer', 'between:0,600'],
        ]);

        [$startHour, $startMinute] = array_map('intval', explode(':', $validated['start_time']));
        [$endHour, $endMinute] = array_map('intval', explode(':', $validated['end_time']));
        $startMinutes = ($startHour * 60) + $startMinute;
        $endMinutes = ($endHour * 60) + $endMinute;
        $scheduledMinutes = ($endMinutes - $startMinutes + 1440) % 1440;

        if ($scheduledMinutes === 0) {
            throw ValidationException::withMessages([
                'end_time' => '終了時刻は開始時刻と異なる値を指定してください。',
            ]);
        }

        if ($validated['planned_break_minutes'] >= $scheduledMinutes && $validated['planned_break_minutes'] > 0) {
            throw ValidationException::withMessages([
                'planned_break_minutes' => '予定休憩は予定勤務時間より短くしてください。',
            ]);
        }

        $weekdays = array_values(array_unique(array_map('intval', $validated['weekdays'])));
        sort($weekdays);

        $schedule = AttendanceSchedule::query()->updateOrCreate(
            [
                'user_id' => $validated['user_id'],
                'effective_from' => $validated['effective_from'],
            ],
            [
                'weekdays' => $weekdays,
                'start_time' => $validated['start_time'],
                'end_time' => $validated['end_time'],
                'planned_break_minutes' => $validated['planned_break_minutes'],
            ],
        );

        return response()->json([
            'data' => $this->serialize($schedule),
        ]);
    }

    private function authorizeAdmin(Request $request): void
    {
        abort_unless($request->user()->role === 'admin', 403);
    }

    private function targetEmployee(Request $request): User
    {
        if ($request->user()->role !== 'admin') {
            abort_if($request->query->has('user_id'), 403);

            return $request->user();
        }

        $validated = $request->validate([
            'user_id' => [
                'required',
                'integer',
                Rule::exists('users', 'id')
                    ->where('role', 'user')
                    ->where('status', 'active'),
            ],
        ]);

        return User::query()->findOrFail($validated['user_id']);
    }

    private function serialize(AttendanceSchedule $schedule): array
    {
        return [
            'id' => $schedule->id,
            'effective_from' => $schedule->effective_from->toDateString(),
            'weekdays' => $schedule->weekdays,
            'start_time' => substr($schedule->start_time, 0, 5),
            'end_time' => substr($schedule->end_time, 0, 5),
            'planned_break_minutes' => $schedule->planned_break_minutes,
        ];
    }
}
