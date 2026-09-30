<?php

namespace App\Http\Resources\Tickets;

use App\Http\Resources\Users\UserSummaryResource;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class TicketCommentResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => (string) $this->id,
            'body' => $this->body,
            'author' => new UserSummaryResource($this->whenLoaded('user')),
            'created_at' => $this->created_at?->toISOString(),
            'updated_at' => $this->updated_at?->toISOString(),
        ];
    }
}
