<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Tickets\TicketController;

/*
|--------------------------------------------------------------------------
| Ticket API Routes (/api/tickets/*)
|--------------------------------------------------------------------------
*/

Route::get('/', [TicketController::class, 'index']);
Route::post('/', [TicketController::class, 'store']);
Route::get('/{ticket}', [TicketController::class, 'show']);
Route::patch('/{ticket}', [TicketController::class, 'updateStatus']);
Route::delete('/{ticket}', [TicketController::class, 'destroy']);