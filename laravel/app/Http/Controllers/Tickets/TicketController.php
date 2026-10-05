<?php

namespace App\Http\Controllers\Tickets;

use App\Http\Controllers\Controller;
use App\Http\Resources\Tickets\TicketResource;
use App\Models\Project;
use App\Models\Ticket;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\Rule;

class TicketController extends Controller
{
    private const STATUSES = ['BACKLOG', 'TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE'];

    public function index(Request $request)
    {
        $user = $request->user();

        $tickets = Ticket::query()
            ->with(['project:id,name', 'assignee:id,name'])
            ->when(
                $user->role !== 'admin',
                fn ($query) => $query->whereHas(
                    'project.members',
                    fn ($members) => $members->where('users.id', $user->id)
                )
            )
            ->orderBy('project_id')
            ->orderBy('status')
            ->orderBy('position')
            ->orderBy('id')
            ->get();

        return TicketResource::collection($tickets);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'project_id' => ['required', 'integer', 'exists:projects,id'],
            'title' => ['required', 'string', 'max:255'],
            'description' => ['nullable', 'string'],
            'status' => ['sometimes', Rule::in(self::STATUSES)],
            'priority' => ['sometimes', Rule::in(['HIGHEST', 'HIGH', 'MEDIUM', 'LOW', 'LOWEST'])],
            'assignee_id' => ['nullable', 'integer', 'exists:users,id'],
        ]);

        $project = Project::findOrFail($validated['project_id']);
        $this->authorizeProjectWrite($request, $project);
        $this->validateAssignee($project, $validated['assignee_id'] ?? null);

        $ticket = DB::transaction(function () use ($validated) {
            $project = Project::query()->lockForUpdate()->findOrFail($validated['project_id']);
            $status = $validated['status'] ?? 'TODO';
            $position = (int) Ticket::query()
                ->where('project_id', $project->id)
                ->where('status', $status)
                ->max('position') + 1;

            $ticket = Ticket::create([
                'project_id' => $project->id,
                'title' => $validated['title'],
                'description' => $validated['description'] ?? null,
                'status' => $status,
                'position' => $position,
                'priority' => $validated['priority'] ?? 'MEDIUM',
                'assignee_id' => $validated['assignee_id'] ?? null,
            ]);

            $ticket->update(['issue_key' => 'TICK-'.$ticket->id]);
            $project->increment('board_version');

            return $ticket;
        });

        return (new TicketResource($ticket->load(['project:id,name', 'assignee:id,name'])))
            ->response()
            ->setStatusCode(201);
    }

    public function show(Request $request, Ticket $ticket)
    {
        $this->authorizeProjectRead($request, $ticket->project);

        return new TicketResource($ticket->load(['project:id,name', 'assignee:id,name']));
    }

    public function updateStatus(Request $request, Ticket $ticket)
    {
        $this->authorizeProjectWrite($request, $ticket->project);

        $validated = $request->validate([
            'title' => ['sometimes', 'required', 'string', 'max:255'],
            'description' => ['sometimes', 'nullable', 'string'],
            'status' => ['sometimes', 'required', Rule::in(self::STATUSES)],
            'priority' => ['sometimes', 'required', Rule::in(['HIGHEST', 'HIGH', 'MEDIUM', 'LOW', 'LOWEST'])],
            'assignee_id' => ['sometimes', 'nullable', 'integer', 'exists:users,id'],
        ]);

        if (array_key_exists('assignee_id', $validated)) {
            $this->validateAssignee($ticket->project, $validated['assignee_id']);
        }

        $statusChanged = isset($validated['status']) && $validated['status'] !== $ticket->status;

        if (! $statusChanged) {
            $ticket->update($validated);

            return new TicketResource($ticket->load(['project:id,name', 'assignee:id,name']));
        }

        DB::transaction(function () use ($ticket, $validated) {
            $project = Project::query()->lockForUpdate()->findOrFail($ticket->project_id);
            $sourceStatus = $ticket->status;
            $newPosition = (int) Ticket::query()
                ->where('project_id', $project->id)
                ->where('status', $validated['status'])
                ->max('position') + 1;

            $ticket->update([...$validated, 'position' => $newPosition]);
            $this->compactColumn($project->id, $sourceStatus);
            $project->increment('board_version');
        });

        return new TicketResource($ticket->refresh()->load(['project:id,name', 'assignee:id,name']));
    }

    public function move(Request $request, Ticket $ticket)
    {
        $this->authorizeProjectWrite($request, $ticket->project);

        $validated = $request->validate([
            'status' => ['required', Rule::in(self::STATUSES)],
            'position' => ['required', 'integer', 'min:0'],
            'board_version' => ['required', 'integer', 'min:0'],
        ]);

        $project = DB::transaction(function () use ($ticket, $validated) {
            $project = Project::query()->lockForUpdate()->findOrFail($ticket->project_id);

            abort_if(
                (int) $project->board_version !== (int) $validated['board_version'],
                409,
                'The ticket board has changed. Refresh and try again.'
            );

            $ticket->refresh();
            $sourceStatus = $ticket->status;
            $targetStatus = $validated['status'];

            $sourceIds = Ticket::query()
                ->where('project_id', $project->id)
                ->where('status', $sourceStatus)
                ->whereKeyNot($ticket->id)
                ->orderBy('position')
                ->orderBy('id')
                ->pluck('id')
                ->all();

            if ($sourceStatus === $targetStatus) {
                $targetIds = $sourceIds;
            } else {
                $targetIds = Ticket::query()
                    ->where('project_id', $project->id)
                    ->where('status', $targetStatus)
                    ->orderBy('position')
                    ->orderBy('id')
                    ->pluck('id')
                    ->all();
                $this->writePositions($sourceIds);
            }

            $position = min((int) $validated['position'], count($targetIds));
            array_splice($targetIds, $position, 0, [$ticket->id]);

            $ticket->update(['status' => $targetStatus]);
            $this->writePositions($targetIds);
            $project->increment('board_version');

            return $project->refresh();
        });

        return (new TicketResource($ticket->refresh()->load(['project:id,name', 'assignee:id,name'])))
            ->additional(['board_version' => (int) $project->board_version]);
    }

    public function destroy(Request $request, Ticket $ticket): JsonResponse
    {
        $this->authorizeProjectWrite($request, $ticket->project);

        DB::transaction(function () use ($ticket) {
            $project = Project::query()->lockForUpdate()->findOrFail($ticket->project_id);
            $status = $ticket->status;

            $ticket->delete();
            $this->compactColumn($project->id, $status);
            $project->increment('board_version');
        });

        return response()->json(['message' => 'Ticket deleted successfully'], 200);
    }

    private function compactColumn(int $projectId, string $status): void
    {
        $ids = Ticket::query()
            ->where('project_id', $projectId)
            ->where('status', $status)
            ->orderBy('position')
            ->orderBy('id')
            ->pluck('id')
            ->all();

        $this->writePositions($ids);
    }

    /**
     * @param array<int, int> $ticketIds
     */
    private function writePositions(array $ticketIds): void
    {
        foreach ($ticketIds as $position => $ticketId) {
            Ticket::query()->whereKey($ticketId)->update(['position' => $position]);
        }
    }

    private function authorizeProjectRead(Request $request, Project $project): void
    {
        if ($request->user()->role === 'admin') {
            return;
        }

        abort_unless(
            $project->members()->where('users.id', $request->user()->id)->exists(),
            403
        );
    }

    private function authorizeProjectWrite(Request $request, Project $project): void
    {
        if ($request->user()->role === 'admin') {
            return;
        }

        abort_unless(
            $project->members()
                ->where('users.id', $request->user()->id)
                ->wherePivot('permission', 'write')
                ->exists(),
            403
        );
    }

    private function validateAssignee(Project $project, ?int $assigneeId): void
    {
        if ($assigneeId === null) {
            return;
        }

        abort_unless(
            $project->members()->where('users.id', $assigneeId)->exists(),
            422,
            'The assignee must be a member of the project.'
        );
    }
}
