<?php

namespace App\Http\Controllers\Attendance;

use App\Http\Controllers\Controller;
use App\Http\Resources\Attendance\AttendanceRecordResource;
use App\Models\User;
use Carbon\CarbonImmutable;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class AttendanceController extends Controller
{
    private const TIMEZONE = 'Asia/Tokyo';

    public function today(Request $request): JsonResponse
    {
        $date = CarbonImmutable::now(self::TIMEZONE)->toDateString();
        $records = $request->user()->attendanceRecords()->with('breaks');

        $record = (clone $records)->whereNull('clock_out_at')->latest('clock_in_at')->first()
            ?? $records->whereDate('work_date', $date)->first();

        $activeBreak = $record?->breaks->contains(
            fn ($break) => $break->ended_at === null,
        ) ?? false;

        $status = match (true) {
            $record === null => 'not_started',
            $record->clock_out_at === null && $activeBreak => 'on_break',
            $record->clock_out_at === null => 'working',
            default => 'finished',
        };

        return response()->json([
            'data' => [
                'date' => $date,
                'timezone' => self::TIMEZONE,
                'status' => $status,
                'record' => $record === null
                    ? null
                    : (new AttendanceRecordResource($record))->resolve($request),
            ],
        ]);
    }

    public function index(Request $request)
    {
        return AttendanceRecordResource::collection(
            $request->user()->attendanceRecords()
                ->with('breaks')
                ->orderByDesc('work_date')
                ->orderByDesc('id')
                ->paginate(30),
        );
    }

    public function clockIn(Request $request)
    {
        $now = CarbonImmutable::now('UTC');
        $workDate = $now->setTimezone(self::TIMEZONE)->toDateString();

        try {
            $record = DB::transaction(function () use ($request, $now, $workDate) {
                $user = User::query()->whereKey($request->user()->getKey())
                    ->lockForUpdate()
                    ->firstOrFail();

                $records = $user->attendanceRecords();
                if (
                    (clone $records)->whereNull('clock_out_at')->exists()
                    || $records->whereDate('work_date', $workDate)->exists()
                ) {
                    return null;
                }

                return $user->attendanceRecords()->create([
                    'work_date' => $workDate,
                    'clock_in_at' => $now,
                ]);
            });
        } catch (UniqueConstraintViolationException) {
            return $this->conflict('already_clocked_in', '本日はすでに出勤しています。');
        }

        if ($record === null) {
            return $this->conflict('already_clocked_in', '出勤中、または本日はすでに出勤しています。');
        }

        return (new AttendanceRecordResource($record->load('breaks')))->response()->setStatusCode(201);
    }

    public function clockOut(Request $request)
    {
        $now = CarbonImmutable::now('UTC');

        $result = DB::transaction(function () use ($request, $now) {
            $user = User::query()->whereKey($request->user()->getKey())
                ->lockForUpdate()
                ->firstOrFail();

            $openRecord = $user->attendanceRecords()
                ->whereNull('clock_out_at')
                ->latest('clock_in_at')
                ->first();

            if ($openRecord === null) {
                return ['error' => 'not_working'];
            }

            if ($openRecord->breaks()->whereNull('ended_at')->exists()) {
                return ['error' => 'break_in_progress'];
            }

            $updated = $user->attendanceRecords()
                ->whereKey($openRecord->getKey())
                ->whereNull('clock_out_at')
                ->update(['clock_out_at' => $now]);

            return $updated === 0
                ? ['error' => 'not_working']
                : ['record' => $openRecord->refresh()->load('breaks')];
        });

        if (($result['error'] ?? null) === 'break_in_progress') {
            return $this->conflict('break_in_progress', '休憩を終了してから退勤してください。');
        }

        if (($result['error'] ?? null) !== null) {
            return $this->conflict('not_working', '退勤できる出勤記録がありません。');
        }

        return new AttendanceRecordResource($result['record']);
    }

    public function startBreak(Request $request): JsonResponse
    {
        $now = CarbonImmutable::now('UTC');

        $result = DB::transaction(function () use ($request, $now) {
            $user = User::query()->whereKey($request->user()->getKey())
                ->lockForUpdate()
                ->firstOrFail();

            $record = $user->attendanceRecords()
                ->whereNull('clock_out_at')
                ->latest('clock_in_at')
                ->first();

            if ($record === null) {
                return ['error' => 'not_working'];
            }

            if ($record->breaks()->whereNull('ended_at')->exists()) {
                return ['error' => 'already_on_break'];
            }

            return ['break' => $record->breaks()->create(['started_at' => $now])];
        });

        if (isset($result['error'])) {
            $messages = [
                'not_working' => '休憩を開始できる出勤記録がありません。',
                'already_on_break' => 'すでに休憩中です。',
            ];

            return $this->conflict($result['error'], $messages[$result['error']]);
        }

        $break = $result['break'];

        return response()->json([
            'data' => [
                'id' => $break->id,
                'started_at' => $break->started_at->toImmutable()->utc()->toIso8601String(),
                'ended_at' => null,
            ],
        ], 201);
    }

    public function endBreak(Request $request): JsonResponse
    {
        $now = CarbonImmutable::now('UTC');

        $result = DB::transaction(function () use ($request, $now) {
            $user = User::query()->whereKey($request->user()->getKey())
                ->lockForUpdate()
                ->firstOrFail();

            $record = $user->attendanceRecords()
                ->whereNull('clock_out_at')
                ->latest('clock_in_at')
                ->first();

            if ($record === null) {
                return ['error' => 'not_working'];
            }

            $break = $record->breaks()->whereNull('ended_at')->latest('started_at')->first();
            if ($break === null) {
                return ['error' => 'not_on_break'];
            }

            $updated = $record->breaks()
                ->whereKey($break->getKey())
                ->whereNull('ended_at')
                ->update(['ended_at' => $now]);

            return $updated === 0 ? ['error' => 'not_on_break'] : ['break' => $break->refresh()];
        });

        if (isset($result['error'])) {
            $messages = [
                'not_working' => '休憩を終了できる出勤記録がありません。',
                'not_on_break' => '終了できる休憩記録がありません。',
            ];

            return $this->conflict($result['error'], $messages[$result['error']]);
        }

        $break = $result['break'];

        return response()->json([
            'data' => [
                'id' => $break->id,
                'started_at' => $break->started_at->toImmutable()->utc()->toIso8601String(),
                'ended_at' => $break->ended_at->toImmutable()->utc()->toIso8601String(),
            ],
        ]);
    }

    private function conflict(string $code, string $message): JsonResponse
    {
        return response()->json([
            'message' => $message,
            'code' => $code,
        ], 409);
    }
}
