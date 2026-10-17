<?php

namespace Tests\Feature\Ticket\Concerns;

use App\Models\Project;
use App\Models\User;

trait UsesGeneralProject
{
    protected function addToGeneralProject(
        User $user,
        string $role = 'member',
        string $permission = 'write',
    ): Project {
        $project = Project::query()->where('name', 'General')->firstOrFail();
        $this->addProjectMember($project, $user, $role, $permission);

        return $project;
    }

    protected function addProjectMember(
        Project $project,
        User $user,
        string $role = 'member',
        string $permission = 'write',
    ): void {
        $project->members()->syncWithoutDetaching([
            $user->id => compact('role', 'permission'),
        ]);
    }
}
