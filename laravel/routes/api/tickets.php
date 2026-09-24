<?php

use App\Http\Controllers\Tickets\TicketController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Ticket API Routes (/api/tickets/*)
|--------------------------------------------------------------------------
*/

Route::middleware([
    'auth:sanctum',
    'active.user',
])->group(function () {
    Route::get('/', [TicketController::class, 'index']);
    Route::post('/', [TicketController::class, 'store']);
    Route::get('/{ticket}', [TicketController::class, 'show']);
    Route::patch('/{ticket}', [TicketController::class, 'updateStatus']);
    Route::delete('/{ticket}', [TicketController::class, 'destroy']);
});