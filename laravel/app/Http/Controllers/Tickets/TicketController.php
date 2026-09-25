<?php

namespace App\Http\Controllers\Tickets;

use App\Http\Controllers\Controller;
use App\Http\Resources\Tickets\TicketResource;
use App\Models\Ticket;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class TicketController extends Controller
{
    /**
     * GET /api/tickets
     */
    public function index()
    {
        $tickets = Ticket::with('assignee:id,name')
            ->orderBy('id', 'asc')
            ->get();

        return TicketResource::collection($tickets);
    }

    /**
     * POST /api/tickets
     */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'title' => 'required|string|max:255',
            'description' => 'nullable|string',
            'status' => 'sometimes|in:BACKLOG,TODO,IN_PROGRESS,IN_REVIEW,DONE',
            'priority' => 'sometimes|in:HIGHEST,HIGH,MEDIUM,LOW,LOWEST',
            'assignee_id' => 'nullable|exists:users,id',
        ]);

        $ticket = DB::transaction(function () use ($validated) {
            $ticket = Ticket::create([
                'title' => $validated['title'],
                'description' => $validated['description'] ?? null,
                'status' => $validated['status'] ?? 'TODO',
                'priority' => $validated['priority'] ?? 'MEDIUM',
                'assignee_id' => $validated['assignee_id'] ?? null,
            ]);

            $ticket->update([
                'issue_key' => 'TICK-'.$ticket->id,
            ]);

            return $ticket;
        });

        return (new TicketResource($ticket->load('assignee:id,name')))
            ->response()
            ->setStatusCode(201);
    }

    /**
     * GET /api/tickets/{ticket}
     */
    public function show(Ticket $ticket)
    {
        return new TicketResource($ticket->load('assignee:id,name'));
    }

    /**
     * PATCH /api/tickets/{ticket}
     */
    public function updateStatus(Request $request, Ticket $ticket)
    {
        $validated = $request->validate([
            'status' => 'required|in:BACKLOG,TODO,IN_PROGRESS,IN_REVIEW,DONE',
        ]);

        $ticket->update([
            'status' => $validated['status'],
        ]);

        return new TicketResource($ticket->load('assignee:id,name'));
    }

    /**
     * DELETE /api/tickets/{ticket}
     */
    public function destroy(Ticket $ticket): JsonResponse
    {
        $ticket->delete();

        return response()->json([
            'message' => 'Ticket deleted successfully',
        ], 200);
    }
}
