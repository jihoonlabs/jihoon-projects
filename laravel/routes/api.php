<?php

// Controller import (Vue import)
use App\Http\Controllers\NoticeController;

// Route 기능 사용 (라우팅 정의용)
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
| 이 파일은 "API용 URL → Controller 연결"을 정의하는 곳
| 모든 URL 앞에는 자동으로 /api 가 붙는다
| 예: /notices → 실제는 /api/notices
|--------------------------------------------------------------------------
*/

// /api/notices 로 시작하는 그룹 생성
Route::prefix('notices')->group(function () {

    /*
    |--------------------------------------------------------------------------
    | GET /api/notices
    |--------------------------------------------------------------------------
    | 공지 목록 조회
    | Vue: axios.get('/api/notices')
    | Controller: NoticeController@index 실행
    */
    Route::get('/', [NoticeController::class, 'index']);

    /*
    |--------------------------------------------------------------------------
    | GET /api/notices/{id}
    |--------------------------------------------------------------------------
    | 공지 상세 조회
    | {id}는 변수 (예: /api/notices/1)
    | Vue: axios.get('/api/notices/1')
    | Controller: NoticeController@show 실행
    */
    Route::get('/{id}', [NoticeController::class, 'show']);

    /*
    |--------------------------------------------------------------------------
    | POST /api/notices
    |--------------------------------------------------------------------------
    | 공지 생성
    | Vue:
    | axios.post('/api/notices', { title, content })
    | Controller: NoticeController@store 실행
    */
    Route::post('/', [NoticeController::class, 'store']);

    /*
    |--------------------------------------------------------------------------
    | PUT /api/notices/{id}
    |--------------------------------------------------------------------------
    | 공지 수정
    | Vue:
    | axios.put('/api/notices/1', { title })
    | Controller: NoticeController@update 실행
    */
    Route::put('/{id}', [NoticeController::class, 'update']);

    /*
    |--------------------------------------------------------------------------
    | DELETE /api/notices/{id}
    |--------------------------------------------------------------------------
    | 공지 삭제
    | Vue:
    | axios.delete('/api/notices/1')
    | Controller: NoticeController@destroy 실행
    */
    Route::delete('/{id}', [NoticeController::class, 'destroy']);
});