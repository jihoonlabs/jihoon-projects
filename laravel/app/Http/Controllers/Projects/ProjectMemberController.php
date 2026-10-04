<?php

namespace App\Http\Controllers\Projects;

use App\Http\Controllers\Controller;
use App\Http\Resources\Projects\ProjectMemberResource;
use App\Models\Project;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class ProjectMemberController extends Controller
{
    public function index(Request $request, Project $project)
    {
        $this->authorizeRead($request, $project);

        return ProjectMemberResource::collection(
            $project->members()->orderBy('name')->get()
        );
    }

    public function store(Request $request, Project $project)
    {
        $this->authorizeManage($request, $project);
        $validated = $request->validate([
            'email' => ['required', 'email', 'exists:users,email'],
            'role' => ['required', Rule::in(['leader', 'member'])],
            'permission' => ['required', Rule::in(['read', 'write'])],
        ]);
        $user = User::query()->where('email', $validated['email'])->firstOrFail();

        abort_if(
            $project->members()->where('users.id', $user->id)->exists(),
            409,
            'User is already a project member.'
        );

        $project->members()->attach($user, [
            'role' => $validated['role'],
            'permission' => $validated['permission'],
        ]);

        $member = $project->members()->where('users.id', $user->id)->firstOrFail();

        return (new ProjectMemberResource($member))->response()->setStatusCode(201);
    }

    public function update(Request $request, Project $project, User $user): ProjectMemberResource
    {
        $this->authorizeManage($request, $project);
        $validated = $request->validate([
            'role' => ['required', Rule::in(['leader', 'member'])],
            'permission' => ['required', Rule::in(['read', 'write'])],
        ]);

        abort_unless(
            $project->members()->where('users.id', $user->id)->exists(),
            404
        );

        $project->members()->updateExistingPivot($user->id, $validated);
        $member = $project->members()->where('users.id', $user->id)->firstOrFail();

        return new ProjectMemberResource($member);
    }

    public function destroy(Request $request, Project $project, User $user)
    {
        $this->authorizeManage($request, $project);
        $detached = $project->members()->detach($user->id);
        abort_unless($detached > 0, 404);

        return response()->noContent();
    }

    private function authorizeRead(Request $request, Project $project): void
    {
        if ($request->user()->role === 'admin') {
            return;
        }

        abort_unless(
            $project->members()->where('users.id', $request->user()->id)->exists(),
            403
        );
    }

    private function authorizeManage(Request $request, Project $project): void
    {
        if ($request->user()->role === 'admin') {
            return;
        }

        abort_unless(
            $project->members()
                ->where('users.id', $request->user()->id)
                ->wherePivot('role', 'leader')
                ->exists(),
            403
        );
    }
}
