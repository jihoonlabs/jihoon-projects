<?php

use App\Http\Controllers\Tickets\TicketCommentController;
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
    Route::patch('/{ticket}/move', [TicketController::class, 'move']);
    Route::patch('/{ticket}', [TicketController::class, 'updateStatus']);
    Route::delete('/{ticket}', [TicketController::class, 'destroy']);
    Route::get('/{ticket}/comments', [TicketCommentController::class, 'index']);
    Route::post('/{ticket}/comments', [TicketCommentController::class, 'store']);
    Route::patch('/{ticket}/comments/{comment}', [TicketCommentController::class, 'update']);
    Route::delete('/{ticket}/comments/{comment}', [TicketCommentController::class, 'destroy']);
});
