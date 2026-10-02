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
            ->orderBy('id', 'asc')
            ->get();

        return TicketResource::collection($tickets);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'project_id' => ['required', 'integer', 'exists:projects,id'],
            'title' => ['required', 'string', 'max:255'],
            'description' => ['nullable', 'string'],
            'status' => ['sometimes', Rule::in(['BACKLOG', 'TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE'])],
            'priority' => ['sometimes', Rule::in(['HIGHEST', 'HIGH', 'MEDIUM', 'LOW', 'LOWEST'])],
            'assignee_id' => ['nullable', 'integer', 'exists:users,id'],
        ]);

        $project = Project::findOrFail($validated['project_id']);
        $this->authorizeProjectWrite($request, $project);
        $this->validateAssignee($project, $validated['assignee_id'] ?? null);

        $ticket = DB::transaction(function () use ($validated) {
            $ticket = Ticket::create([
                'project_id' => $validated['project_id'],
                'title' => $validated['title'],
                'description' => $validated['description'] ?? null,
                'status' => $validated['status'] ?? 'TODO',
                'priority' => $validated['priority'] ?? 'MEDIUM',
                'assignee_id' => $validated['assignee_id'] ?? null,
            ]);

            $ticket->update(['issue_key' => 'TICK-'.$ticket->id]);

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
            'status' => ['sometimes', 'required', Rule::in(['BACKLOG', 'TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE'])],
            'priority' => ['sometimes', 'required', Rule::in(['HIGHEST', 'HIGH', 'MEDIUM', 'LOW', 'LOWEST'])],
            'assignee_id' => ['sometimes', 'nullable', 'integer', 'exists:users,id'],
        ]);

        if (array_key_exists('assignee_id', $validated)) {
            $this->validateAssignee($ticket->project, $validated['assignee_id']);
        }

        $ticket->update($validated);

        return new TicketResource($ticket->load(['project:id,name', 'assignee:id,name']));
    }

    public function destroy(Request $request, Ticket $ticket): JsonResponse
    {
        $this->authorizeProjectWrite($request, $ticket->project);
        $ticket->delete();

        return response()->json(['message' => 'Ticket deleted successfully'], 200);
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
