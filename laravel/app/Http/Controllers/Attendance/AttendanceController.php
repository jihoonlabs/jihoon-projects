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
        $records = $request->user()->attendanceRecords();
        $record = (clone $records)->whereNull('clock_out_at')->latest('clock_in_at')->first()
            ?? $records->whereDate('work_date', $date)->first();

        $status = match (true) {
            $record === null => 'not_started',
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
                ->orderByDesc('work_date')
                ->orderByDesc('id')
                ->paginate(30),
        );
    }

    public function clockIn(Request $request)
    {
        $now = CarbonImmutable::now('UTC');
        $date = $now->setTimezone(self::TIMEZONE)->toDateString();

        try {
            $record = DB::transaction(function () use ($request, $now, $date) {
                $user = User::query()->whereKey($request->user()->getKey())
                    ->lockForUpdate()->firstOrFail();

                if ($user->attendanceRecords()->whereNull('clock_out_at')->exists()
                    || $user->attendanceRecords()->whereDate('work_date', $date)->exists()) {
                    return null;
                }

                return $user->attendanceRecords()->create([
                    'work_date' => $date,
                    'clock_in_at' => $now,
                ]);
            });
        } catch (UniqueConstraintViolationException) {
            return $this->conflict('already_clocked_in', '本日はすでに出勤しています。');
        }

        if ($record === null) {
            return $this->conflict('already_clocked_in', '出勤中、または本日はすでに出勤しています。');
        }

        return (new AttendanceRecordResource($record))->response()->setStatusCode(201);
    }

    public function clockOut(Request $request)
    {
        $now = CarbonImmutable::now('UTC');
        $record = DB::transaction(function () use ($request, $now) {
            $user = User::query()->whereKey($request->user()->getKey())
                ->lockForUpdate()->firstOrFail();
            $openRecord = $user->attendanceRecords()
                ->whereNull('clock_out_at')
                ->latest('clock_in_at')
                ->first();

            if ($openRecord === null) {
                return null;
            }

            $updated = $user->attendanceRecords()
                ->whereKey($openRecord->getKey())
                ->whereNull('clock_out_at')
                ->update(['clock_out_at' => $now]);

            if ($updated === 0) {
                return null;
            }

            return $openRecord->refresh();
        });

        if ($record === null) {
            return $this->conflict('not_working', '退勤できる出勤記録がありません。');
        }

        return new AttendanceRecordResource($record);
    }

    private function conflict(string $code, string $message): JsonResponse
    {
        return response()->json([
            'message' => $message,
            'code' => $code,
        ], 409);
    }
}
