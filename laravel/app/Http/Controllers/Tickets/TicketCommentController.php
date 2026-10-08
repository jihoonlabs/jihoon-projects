<?php

namespace App\Http\Controllers\Tickets;

use App\Http\Controllers\Controller;
use App\Http\Resources\Tickets\TicketCommentResource;
use App\Models\Project;
use App\Models\Ticket;
use App\Models\TicketComment;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\DB;

class TicketCommentController extends Controller
{
    public function index(Request $request, Ticket $ticket): AnonymousResourceCollection
    {
        $this->authorizeProjectRead($request, $ticket);

        return TicketCommentResource::collection(
            $ticket->comments()->with('user')->oldest()->get()
        );
    }

    public function store(Request $request, Ticket $ticket): TicketCommentResource
    {
        $this->authorizeProjectRead($request, $ticket);
        $this->ensureActive($ticket);
        $validated = $this->validateBody($request);

        $comment = DB::transaction(function () use ($ticket, $request, $validated) {
            $this->lockActiveProject($ticket);
            $comment = $ticket->comments()->make(['body' => $validated['body']]);
            $comment->user()->associate($request->user());
            $comment->save();

            return $comment;
        });

        return new TicketCommentResource($comment->load('user'));
    }

    public function update(Request $request, Ticket $ticket, TicketComment $comment): TicketCommentResource
    {
        $this->authorizeProjectRead($request, $ticket);
        $this->ensureActive($ticket);
        $this->ensureCommentBelongsToTicket($ticket, $comment);
        abort_unless($comment->user_id === $request->user()->id, 403);

        $validated = $this->validateBody($request);

        DB::transaction(function () use ($ticket, $comment, $validated) {
            $this->lockActiveProject($ticket);
            $comment->update(['body' => $validated['body']]);
        });

        return new TicketCommentResource($comment->load('user'));
    }

    public function destroy(Request $request, Ticket $ticket, TicketComment $comment): Response
    {
        $this->authorizeProjectRead($request, $ticket);
        $this->ensureActive($ticket);
        $this->ensureCommentBelongsToTicket($ticket, $comment);
        abort_unless(
            $comment->user_id === $request->user()->id || $request->user()->role === 'admin',
            403
        );

        DB::transaction(function () use ($ticket, $comment) {
            $this->lockActiveProject($ticket);
            $comment->delete();
        });

        return response()->noContent();
    }

    private function authorizeProjectRead(Request $request, Ticket $ticket): void
    {
        if ($request->user()->role === 'admin') {
            return;
        }

        abort_unless(
            $ticket->project->members()->where('users.id', $request->user()->id)->exists(),
            403
        );
    }

    private function ensureActive(Ticket $ticket): void
    {
        abort_if($ticket->project->archived_at !== null, 409, 'Restore this project before changing comments.');
    }

    private function lockActiveProject(Ticket $ticket): void
    {
        $project = Project::query()->whereKey($ticket->project_id)->lockForUpdate()->firstOrFail();
        abort_if($project->archived_at !== null, 409, 'Restore this project before changing comments.');
    }

    private function validateBody(Request $request): array
    {
        if (is_string($request->input('body'))) {
            $request->merge(['body' => trim($request->input('body'))]);
        }

        return $request->validate([
            'body' => ['required', 'string', 'max:5000'],
        ]);
    }

    private function ensureCommentBelongsToTicket(Ticket $ticket, TicketComment $comment): void
    {
        abort_unless($comment->ticket_id === $ticket->id, 404);
    }
}
