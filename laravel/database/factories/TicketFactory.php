<?php

namespace Database\Factories;

use App\Models\Ticket;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Ticket>
 */
class TicketFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'issue_key' => fake()->unique()->bothify('TICK-####'),
            'title' => fake()->sentence(),
            'description' => fake()->paragraph(),
            'status' => 'TODO',
            'priority' => 'MEDIUM',
            'assignee_id' => null,
        ];
    }
}
