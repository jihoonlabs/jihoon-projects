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
        $validated = $request->validate([
            'archived' => ['sometimes', 'boolean'],
            'search' => ['sometimes', 'string', 'max:255'],
        ]);
        $archived = (bool) ($validated['archived'] ?? false);
        $search = trim($validated['search'] ?? '');

        $projects = Project::query()
            ->when($archived, fn ($query) => $query->whereNotNull('archived_at'), fn ($query) => $query->whereNull('archived_at'))
            ->when(
                $request->user()->role !== 'admin',
                fn ($query) => $query->whereHas(
                    'members',
                    fn ($members) => $members->where('users.id', $request->user()->id)
                )
            )
            ->when($search !== '', fn ($query) => $query->where(function ($filter) use ($search) {
                $filter->where('project_key', 'like', strtoupper($search).'%')
                    ->orWhere('name', 'like', '%'.$search.'%');
            }))
            ->orderBy('name')
            ->get();

        return ProjectResource::collection($projects);
    }

    public function store(Request $request): ProjectResource
    {
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:255'],
        ]);

        $attempts = 0;

        while (true) {
            try {
                return new ProjectResource(DB::transaction(function () use ($validated, $request) {
                    $project = new Project($validated);
                    $project->created_by = $request->user()->id;
                    $project->save();
                    $project->members()->attach($request->user()->id, [
                        'role' => 'leader',
                        'permission' => 'write',
                    ]);
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

    public function showByKey(Request $request, string $projectKey): ProjectResource
    {
        abort_unless(preg_match('/^[A-Z]{3}$/', strtoupper($projectKey)) === 1, 404);
        $project = Project::query()->where('project_key', strtoupper($projectKey))->firstOrFail();
        $this->authorizeRead($request, $project);

        return new ProjectResource($project->load('members'));
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

    public function archive(Request $request, Project $project): ProjectResource
    {
        DB::transaction(function () use ($request, $project) {
            $locked = Project::query()->whereKey($project->id)->lockForUpdate()->firstOrFail();
            $this->authorizeManage($request, $locked);
            abort_if($locked->tickets()->where('status', '!=', 'DONE')->exists(), 409, 'Complete all tickets before archiving.');
            if ($locked->archived_at === null) {
                $locked->forceFill(['archived_at' => now()])->save();
                $this->recordAudit($request, $locked, 'project.archived', [
                    'name' => $locked->name,
                ]);
            }
        });

        return new ProjectResource($project->refresh());
    }

    public function restore(Request $request, Project $project): ProjectResource
    {
        DB::transaction(function () use ($request, $project) {
            $locked = Project::query()->whereKey($project->id)->lockForUpdate()->firstOrFail();
            $this->authorizeManage($request, $locked);
            if ($locked->archived_at !== null) {
                $locked->forceFill(['archived_at' => null])->save();
                $this->recordAudit($request, $locked, 'project.restored', [
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

    private function authorizeManage(Request $request, Project $project): void
    {
        if ($request->user()->role === 'admin') {
            return;
        }

        abort_unless(
            $project->members()->where('users.id', $request->user()->id)
                ->wherePivot('role', 'leader')->exists(),
            403
        );
    }

    private function authorizeAdmin(Request $request): void
    {
        abort_unless($request->user()->role === 'admin', 403);
    }
}
