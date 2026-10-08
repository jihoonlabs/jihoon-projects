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
        $validated = $this->validateBody($request);

        $comment = DB::transaction(function () use ($request, $ticket, $validated) {
            $project = $this->lockProject($ticket);
            $comment = $ticket->comments()->make(['body' => $validated['body']]);
            $comment->user()->associate($request->user());
            $comment->save();
            $this->recordCommentAudit($request, $project, $ticket, $comment, 'comment.created');

            return $comment;
        });

        return new TicketCommentResource($comment->load('user'));
    }

    public function update(Request $request, Ticket $ticket, TicketComment $comment): TicketCommentResource
    {
        $this->authorizeProjectRead($request, $ticket);
        $this->ensureCommentBelongsToTicket($ticket, $comment);
        abort_unless($comment->user_id === $request->user()->id, 403);

        $validated = $this->validateBody($request);

        DB::transaction(function () use ($request, $ticket, $comment, $validated) {
            $project = $this->lockProject($ticket);
            $comment->update(['body' => $validated['body']]);
            $this->recordCommentAudit($request, $project, $ticket, $comment, 'comment.updated');
        });

        return new TicketCommentResource($comment->load('user'));
    }

    public function destroy(Request $request, Ticket $ticket, TicketComment $comment): Response
    {
        $this->authorizeProjectRead($request, $ticket);
        $this->ensureCommentBelongsToTicket($ticket, $comment);
        abort_unless(
            $comment->user_id === $request->user()->id || $request->user()->role === 'admin',
            403
        );

        DB::transaction(function () use ($request, $ticket, $comment) {
            $project = $this->lockProject($ticket);
            $this->recordCommentAudit($request, $project, $ticket, $comment, 'comment.deleted');
            $comment->delete();
        });

        return response()->noContent();
    }

    private function lockProject(Ticket $ticket): Project
    {
        // Serialize with archive and ticket writes; the integrated lifecycle guard must be retained.
        return Project::query()->whereKey($ticket->project_id)->lockForUpdate()->firstOrFail();
    }

    private function recordCommentAudit(
        Request $request,
        Project $project,
        Ticket $ticket,
        TicketComment $comment,
        string $action
    ): void {
        DB::table('ticket_audit_events')->insert([
            'project_id' => $project->id,
            'project_key' => $project->project_key,
            'ticket_id' => $ticket->id,
            'issue_key' => $ticket->issue_key,
            'actor_id' => $request->user()->id,
            'actor_name' => $request->user()->name,
            'action' => $action,
            'snapshot' => json_encode([
                'comment_id' => $comment->id,
                'author_id' => $comment->user_id,
                'body' => $comment->body,
                'created_at' => $comment->created_at?->toIso8601String(),
            ], JSON_THROW_ON_ERROR),
            'created_at' => now(),
        ]);
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
