<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Tickets\TicketController;

/*
|--------------------------------------------------------------------------
| Ticket API Routes (/api/tickets/*)
|--------------------------------------------------------------------------
*/

Route::get('/', [TicketController::class, 'index']);
Route::patch('/{ticket}/status', [TicketController::class, 'updateStatus']);