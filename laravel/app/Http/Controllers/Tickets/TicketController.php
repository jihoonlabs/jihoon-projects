<?php

namespace App\Http\Controllers\Tickets;

use App\Http\Controllers\Controller;
use App\Models\Ticket;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class TicketController extends Controller
{
    /**
     * GET /api/tickets
     */
    public function index(): JsonResponse
    {
        $tickets = Ticket::with('assignee:id,name,email')
            ->orderBy('id', 'asc')
            ->get();

        return response()->json($tickets);
    }

    /**
     * POST /api/tickets
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'title' => 'required|string|max:255',
            'description' => 'nullable|string',
            'status' => 'required|in:BACKLOG,TODO,IN_PROGRESS,IN_REVIEW,DONE',
            'priority' => 'required|in:LOW,MEDIUM,HIGH,URGENT',
            'assignee_id' => 'nullable|exists:users,id',
        ]);

        $latestId = Ticket::max('id') ?? 0;
        $issueKey = 'TICK-' . ($latestId + 1);

        $ticket = Ticket::create([
            'title' => $validated['title'],
            'description' => $validated['description'] ?? null,
            'status' => $validated['status'],
            'priority' => $validated['priority'],
            'assignee_id' => $validated['assignee_id'] ?? null,
            'issue_key' => $issueKey,
        ]);

        return response()->json(
            $ticket->load('assignee:id,name,email'),
            201
        );
    }

    /**
     * GET /api/tickets/{ticket}
     */
    public function show(Ticket $ticket): JsonResponse
    {
        return response()->json(
            $ticket->load('assignee:id,name,email')
        );
    }

    /**
     * PATCH /api/tickets/{ticket}
     */
    public function updateStatus(Request $request, Ticket $ticket): JsonResponse
    {
        $validated = $request->validate([
            'status' => 'required|in:BACKLOG,TODO,IN_PROGRESS,IN_REVIEW,DONE',
        ]);

        $ticket->update([
            'status' => $validated['status'],
        ]);

        return response()->json([
            'message' => 'Status updated successfully',
            'ticket' => $ticket->load('assignee:id,name,email'),
        ]);
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