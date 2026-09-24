<?php

namespace App\Http\Controllers\Tickets;

use App\Http\Controllers\Controller;
use App\Models\Ticket;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class TicketController extends Controller
{
    public function index(): JsonResponse
    {
        $tickets = Ticket::with('assignee:id,name,email')
            ->orderBy('id', 'asc')
            ->get();

        return response()->json($tickets);
    }

    /**
     * PATCH /api/tickets/{ticket}/status
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
}