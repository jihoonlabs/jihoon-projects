<?php

namespace App\Http\Controllers\Tickets;

use App\Http\Controllers\Controller;
use App\Models\Ticket;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\DB;

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
                'issue_key' => 'TICK-' . $ticket->id,
            ]);

            return $ticket;
        });

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