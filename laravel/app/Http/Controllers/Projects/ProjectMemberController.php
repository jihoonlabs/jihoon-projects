<?php

namespace App\Http\Controllers\Projects;

use App\Http\Controllers\Controller;
use App\Http\Resources\Projects\ProjectMemberResource;
use App\Models\Project;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
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
            'role' => ['required', Rule::in(['member'])],
            'permission' => ['required', Rule::in(['read', 'write'])],
        ]);
        $user = User::query()->where('email', $validated['email'])->firstOrFail();

        DB::transaction(function () use ($request, $project, $user, $validated) {
            $locked = $this->lockActiveProject($project);
            $this->authorizeManage($request, $locked);
            abort_if(
                $locked->members()->where('users.id', $user->id)->exists(),
                409,
                'User is already a project member.'
            );
            $locked->members()->attach($user, [
                'role' => $validated['role'],
                'permission' => $validated['permission'],
            ]);
        });

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

        DB::transaction(function () use ($request, $project, $user, $validated) {
            $locked = $this->lockActiveProject($project);
            $this->authorizeManage($request, $locked);
            abort_unless($locked->members()->where('users.id', $user->id)->exists(), 404);
            $current = $locked->members()->where('users.id', $user->id)->firstOrFail();
            abort_if(
                $validated['role'] === 'leader' && $current->pivot->role !== 'leader',
                422,
                'Use leader transfer to promote a project member.'
            );
            abort_if($validated['role'] !== $current->pivot->role, 409, 'Use leader transfer to change project roles.');

            $locked->members()->updateExistingPivot($user->id, [
                'permission' => $validated['permission'],
            ]);
        });
        $member = $project->members()->where('users.id', $user->id)->firstOrFail();

        return new ProjectMemberResource($member);
    }

    public function destroy(Request $request, Project $project, User $user)
    {
        $this->authorizeManage($request, $project);
        $detached = DB::transaction(function () use ($request, $project, $user) {
            $locked = $this->lockActiveProject($project);
            $this->authorizeManage($request, $locked);
            abort_if(
                $locked->members()->where('users.id', $user->id)->wherePivot('role', 'leader')->exists(),
                409,
                'Transfer leadership before removing the leader.'
            );

            return $locked->members()->detach($user->id);
        });
        abort_unless($detached > 0, 404);

        return response()->noContent();
    }

    public function transferLeader(Request $request, Project $project, User $user): ProjectMemberResource
    {
        return DB::transaction(function () use ($request, $project, $user) {
            // Serialize leadership changes and reject changes while the project is archived.
            $locked = $this->lockActiveProject($project);
            $this->authorizeManage($request, $locked);
            $current = $locked->members()->wherePivot('role', 'leader')->get();
            abort_unless($current->count() === 1, 409, 'Project must have exactly one leader.');
            abort_unless($locked->members()->where('users.id', $user->id)->exists(), 404);

            if ($current->first()->id !== $user->id) {
                $locked->members()->updateExistingPivot($current->first()->id, ['role' => 'member']);
                $locked->members()->updateExistingPivot($user->id, ['role' => 'leader']);
            }

            return new ProjectMemberResource($locked->members()->where('users.id', $user->id)->firstOrFail());
        });
    }

    private function lockActiveProject(Project $project): Project
    {
        $locked = Project::query()->whereKey($project->id)->lockForUpdate()->firstOrFail();
        abort_if($locked->archived_at !== null, 409, 'Restore this project before managing members.');

        return $locked;
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
