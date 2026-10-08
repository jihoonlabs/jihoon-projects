<?php

namespace App\Http\Controllers\Projects;

use App\Http\Controllers\Controller;
use App\Http\Resources\Projects\ProjectResource;
use App\Models\Project;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

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

        $attempts = 0;

        while (true) {
            try {
                return new ProjectResource(DB::transaction(function () use ($validated, $request) {
                    $project = Project::create($validated);
                    $this->recordAudit($request, $project, 'project.created', [
                        'name' => $project->name,
                    ]);

                    return $project;
                }));
            } catch (UniqueConstraintViolationException $exception) {
                // A concurrent insert can claim the generated key after the existence check.
                // Retry only project_key collisions; other unique constraints must still fail.
                $attempts++;
                if ($attempts >= 5 || ! str_contains(strtolower($exception->getMessage()), 'project_key')) {
                    throw $exception;
                }
            }
        }
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
        DB::transaction(function () use ($request, $project, $validated) {
            $locked = Project::query()->whereKey($project->id)->lockForUpdate()->firstOrFail();
            $previousName = $locked->name;
            $locked->update($validated);
            if ($locked->name !== $previousName) {
                $this->recordAudit($request, $locked, 'project.renamed', [
                    'previous_name' => $previousName,
                    'name' => $locked->name,
                ]);
            }
        });

        return new ProjectResource($project->refresh());
    }

    public function destroy(Request $request, Project $project)
    {
        $this->authorizeAdmin($request);
        DB::transaction(function () use ($request, $project) {
            $locked = Project::query()->whereKey($project->id)->lockForUpdate()->firstOrFail();
            abort_if($locked->tickets()->exists(), 409, 'Projects with tickets cannot be deleted.');
            $this->recordAudit($request, $locked, 'project.deleted', [
                'name' => $locked->name,
                'created_at' => $locked->created_at?->toIso8601String(),
            ]);
            $locked->delete();
        });

        return response()->noContent();
    }

    private function recordAudit(Request $request, Project $project, string $action, array $snapshot): void
    {
        DB::table('project_audit_events')->insert([
            'project_id' => $project->id,
            'project_key' => $project->project_key,
            'actor_id' => $request->user()->id,
            'actor_name' => $request->user()->name,
            'action' => $action,
            'snapshot' => json_encode($snapshot, JSON_THROW_ON_ERROR),
            'created_at' => now(),
        ]);
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
