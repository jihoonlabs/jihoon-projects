<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Facades\DB;

class Project extends Model
{
    use HasFactory;

    protected static function booted(): void
    {
        static::creating(function (Project $project) {
            if ($project->project_key !== null) {
                // Explicit keys (e.g. factories/imports) cannot revive deleted identities.
                if (DB::table('project_audit_events')->where('project_key', $project->project_key)->exists()) {
                    throw new \InvalidArgumentException('This project key is permanently reserved.');
                }

                return;
            }

            // A deleted project's key remains reserved by its durable audit record.
            // Read both sets once, then choose among unused keys without an unbounded retry.
            $reserved = array_fill_keys(
                array_merge(
                    self::query()->pluck('project_key')->all(),
                    DB::table('project_audit_events')->distinct()->pluck('project_key')->all()
                ),
                true
            );

            $capacity = 26 * 26 * 26;
            if (count($reserved) >= $capacity) {
                throw new \RuntimeException('No project keys remain available.');
            }

            $start = random_int(0, $capacity - 1);
            for ($offset = 0; $offset < $capacity; $offset++) {
                $number = ($start + $offset) % $capacity;
                $key = chr(65 + intdiv($number, 676))
                    .chr(65 + intdiv($number % 676, 26))
                    .chr(65 + $number % 26);

                if (! isset($reserved[$key])) {
                    $project->project_key = $key;

                    return;
                }
            }

            throw new \RuntimeException('No project keys remain available.');
        });
    }

    protected function casts(): array
    {
        return ['archived_at' => 'datetime'];
    }

    protected $fillable = [
        'name',
    ];

    public function members(): BelongsToMany
    {
        return $this->belongsToMany(User::class, 'project_members')
            ->withPivot(['role', 'permission'])
            ->withTimestamps();
    }

    public function tickets(): HasMany
    {
        return $this->hasMany(Ticket::class);
    }
}
