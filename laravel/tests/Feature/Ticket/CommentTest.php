<?php

namespace Tests\Feature\Ticket;

use App\Models\Ticket;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class CommentTest extends TestCase
{
    use RefreshDatabase;

    public function test_authenticated_user_can_create_and_list_comments(): void
    {
        $user = User::factory()->create();
        $ticket = Ticket::factory()->create();

        $this->actingAs($user)
            ->postJson("/api/tickets/{$ticket->id}/comments", ['body' => ' first comment '])
            ->assertCreated()
            ->assertJsonPath('data.body', 'first comment')
            ->assertJsonPath('data.author.id', $user->id);

        $this->actingAs($user)
            ->getJson("/api/tickets/{$ticket->id}/comments")
            ->assertOk()
            ->assertJsonCount(1, 'data')
            ->assertJsonPath('data.0.body', 'first comment');
    }

    public function test_comment_body_is_required(): void
    {
        $user = User::factory()->create();
        $ticket = Ticket::factory()->create();

        $this->actingAs($user)
            ->postJson("/api/tickets/{$ticket->id}/comments", ['body' => ''])
            ->assertUnprocessable()
            ->assertJsonValidationErrors('body');
    }

    public function test_whitespace_only_body_is_rejected(): void
    {
        $user = User::factory()->create();
        $ticket = Ticket::factory()->create();

        $this->actingAs($user)
            ->postJson("/api/tickets/{$ticket->id}/comments", ['body' => '   '])
            ->assertUnprocessable()
            ->assertJsonValidationErrors('body');
    }

    public function test_client_cannot_spoof_comment_author(): void
    {
        $user = User::factory()->create();
        $other = User::factory()->create();
        $ticket = Ticket::factory()->create();

        $this->actingAs($user)
            ->postJson("/api/tickets/{$ticket->id}/comments", [
                'body' => 'comment',
                'user_id' => $other->id,
            ])
            ->assertCreated()
            ->assertJsonPath('data.author.id', $user->id);
    }

    public function test_suspended_user_cannot_access_comments(): void
    {
        $user = User::factory()->create(['status' => 'suspended']);
        $ticket = Ticket::factory()->create();

        $this->actingAs($user)
            ->getJson("/api/tickets/{$ticket->id}/comments")
            ->assertForbidden();

        $this->actingAs($user)
            ->postJson("/api/tickets/{$ticket->id}/comments", ['body' => 'comment'])
            ->assertForbidden();
    }

    public function test_only_author_can_update_or_delete_comment(): void
    {
        $author = User::factory()->create();
        $other = User::factory()->create();
        $ticket = Ticket::factory()->create();
        $comment = $ticket->comments()->make(['body' => 'original']);
        $comment->user()->associate($author);
        $comment->save();

        $this->actingAs($other)
            ->patchJson("/api/tickets/{$ticket->id}/comments/{$comment->id}", ['body' => 'changed'])
            ->assertForbidden();

        $this->actingAs($other)
            ->deleteJson("/api/tickets/{$ticket->id}/comments/{$comment->id}")
            ->assertForbidden();

        $this->actingAs($author)
            ->patchJson("/api/tickets/{$ticket->id}/comments/{$comment->id}", ['body' => 'updated'])
            ->assertOk()
            ->assertJsonPath('data.body', 'updated');

        $this->actingAs($author)
            ->deleteJson("/api/tickets/{$ticket->id}/comments/{$comment->id}")
            ->assertNoContent();

        $this->assertDatabaseMissing('ticket_comments', ['id' => $comment->id]);
    }

    public function test_comment_from_another_ticket_is_not_accessible_through_route(): void
    {
        $user = User::factory()->create();
        $ticket = Ticket::factory()->create();
        $otherTicket = Ticket::factory()->create();
        $comment = $otherTicket->comments()->make(['body' => 'other ticket']);
        $comment->user()->associate($user);
        $comment->save();

        $this->actingAs($user)
            ->patchJson("/api/tickets/{$ticket->id}/comments/{$comment->id}", ['body' => 'changed'])
            ->assertNotFound();
    }

    public function test_guest_cannot_access_comments(): void
    {
        $ticket = Ticket::factory()->create();

        $this->getJson("/api/tickets/{$ticket->id}/comments")->assertUnauthorized();
        $this->postJson("/api/tickets/{$ticket->id}/comments", ['body' => 'comment'])->assertUnauthorized();
    }
}
