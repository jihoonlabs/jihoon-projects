<?php

namespace App\Http\Resources\Projects;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class ProjectResource extends JsonResource
{
    /**
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => (string) $this->id,
            'name' => $this->name,
            'project_key' => $this->project_key,
            'created_by' => $this->created_by === null ? null : (string) $this->created_by,
            'board_version' => (int) $this->board_version,
            'members' => ProjectMemberResource::collection($this->whenLoaded('members')),
        ];
    }
}
