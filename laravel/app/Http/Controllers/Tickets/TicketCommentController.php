<?php

namespace App\Http\Controllers\Tickets;

use App\Http\Controllers\Controller;
use App\Http\Resources\Tickets\TicketCommentResource;
use App\Models\Ticket;
use App\Models\TicketComment;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Http\Response;

class TicketCommentController extends Controller
{
    public function index(Ticket $ticket): AnonymousResourceCollection
    {
        return TicketCommentResource::collection(
            $ticket->comments()->with('user')->oldest()->get()
        );
    }

    public function store(Request $request, Ticket $ticket): TicketCommentResource
    {
        $validated = $request->validate([
            'body' => ['required', 'string', 'max:5000'],
        ]);

        $comment = $ticket->comments()->create([
            'user_id' => $request->user()->id,
            'body' => trim($validated['body']),
        ]);

        return new TicketCommentResource($comment->load('user'));
    }

    public function update(Request $request, Ticket $ticket, TicketComment $comment): TicketCommentResource
    {
        $this->ensureCommentBelongsToTicket($ticket, $comment);
        abort_unless($comment->user_id === $request->user()->id, 403);

        $validated = $request->validate([
            'body' => ['required', 'string', 'max:5000'],
        ]);

        $comment->update(['body' => trim($validated['body'])]);

        return new TicketCommentResource($comment->load('user'));
    }

    public function destroy(Request $request, Ticket $ticket, TicketComment $comment): Response
    {
        $this->ensureCommentBelongsToTicket($ticket, $comment);
        abort_unless($comment->user_id === $request->user()->id, 403);

        $comment->delete();

        return response()->noContent();
    }

    private function ensureCommentBelongsToTicket(Ticket $ticket, TicketComment $comment): void
    {
        abort_unless($comment->ticket_id === $ticket->id, 404);
    }
}
