<?php

namespace App\Http\Controllers\Projects;

use App\Http\Controllers\Controller;
use App\Http\Resources\Projects\ProjectResource;
use App\Models\Project;
use Illuminate\Http\Request;

class ProjectController extends Controller
{
    public function index(Request $request)
    {
        $projects = Project::query()
            ->when(
                $request->user()->role !== 'admin',
                fn ($query) => $query->whereHas(
                    'members',
                    fn ($members) => $members->where('users.id', $request->user()->id)
                )
            )
            ->orderBy('name')
            ->get();

        return ProjectResource::collection($projects);
    }

    public function store(Request $request): ProjectResource
    {
        $this->authorizeAdmin($request);
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:255'],
        ]);

        return new ProjectResource(Project::create($validated));
    }

    public function show(Request $request, Project $project): ProjectResource
    {
        $this->authorizeRead($request, $project);

        return new ProjectResource($project->load('members'));
    }

    public function update(Request $request, Project $project): ProjectResource
    {
        $this->authorizeAdmin($request);
        $validated = $request->validate([
            'name' => ['sometimes', 'required', 'string', 'max:255'],
        ]);
        $project->update($validated);

        return new ProjectResource($project->refresh());
    }

    public function destroy(Request $request, Project $project)
    {
        $this->authorizeAdmin($request);
        abort_if($project->tickets()->exists(), 409, 'Projects with tickets cannot be deleted.');

        $project->delete();

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

    private function authorizeAdmin(Request $request): void
    {
        abort_unless($request->user()->role === 'admin', 403);
    }
}
