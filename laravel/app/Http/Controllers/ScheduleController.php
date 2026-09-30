<?php

namespace App\Http\Controllers;

use App\Models\Schedule;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class ScheduleController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'from' => ['required', 'date'],
            'to' => ['required', 'date', 'after_or_equal:from'],
        ]);

        $schedules = $request->user()
            ->schedules()
            ->where('starts_at', '<', $validated['to'])
            ->where('ends_at', '>=', $validated['from'])
            ->orderBy('starts_at')
            ->get();

        return response()->json(['data' => $schedules]);
    }

    public function store(Request $request): JsonResponse
    {
        $validated = $this->validateSchedule($request);

        $schedule = $request->user()->schedules()->create($validated);

        return response()->json(['data' => $schedule], 201);
    }

    public function update(Request $request, Schedule $schedule): JsonResponse
    {
        $this->ensureOwner($request, $schedule);
        $schedule->update($this->validateSchedule($request));

        return response()->json(['data' => $schedule->fresh()]);
    }

    public function destroy(Request $request, Schedule $schedule): JsonResponse
    {
        $this->ensureOwner($request, $schedule);
        $schedule->delete();

        return response()->json(null, 204);
    }

    private function validateSchedule(Request $request): array
    {
        return $request->validate([
            'title' => ['required', 'string', 'max:255'],
            'starts_at' => ['required', 'date'],
            'ends_at' => ['required', 'date', 'after:starts_at'],
            'memo' => ['nullable', 'string'],
        ]);
    }

    private function ensureOwner(Request $request, Schedule $schedule): void
    {
        abort_unless($schedule->user_id === $request->user()->id, 404);
    }
}
