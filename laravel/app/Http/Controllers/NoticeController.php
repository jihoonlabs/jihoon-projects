<?php

namespace App\Http\Controllers;

// 요청 데이터를 받기 위한 클래스
use Illuminate\Http\Request;

class NoticeController extends Controller
{
    /*
    |--------------------------------------------------------------------------
    | GET /api/notices
    |--------------------------------------------------------------------------
    | 공지 목록 반환
    | Vue: axios.get('/api/notices')
    */
    public function index()
    {
        return response()->json([
            'message' => 'notice list',
            'data' => [
                ['id' => 1, 'title' => '공지 1'],
                ['id' => 2, 'title' => '공지 2'],
            ],
        ]);
    }

    /*
    |--------------------------------------------------------------------------
    | GET /api/notices/{id}
    |--------------------------------------------------------------------------
    | 공지 상세 반환
    | Vue: axios.get('/api/notices/1')
    */
    public function show($id)
    {
        return response()->json([
            'message' => 'notice detail',
            'id' => $id,
            'title' => '공지 ' . $id,
        ]);
    }

    /*
    |--------------------------------------------------------------------------
    | POST /api/notices
    |--------------------------------------------------------------------------
    | 공지 생성
    | Vue:
    | axios.post('/api/notices', { title, content })
    */
    public function store(Request $request)
    {
        return response()->json([
            'message' => 'notice created',
            'input' => $request->all(), // 요청 데이터 확인
        ], 201);
    }

    /*
    |--------------------------------------------------------------------------
    | PUT /api/notices/{id}
    |--------------------------------------------------------------------------
    | 공지 수정
    | Vue:
    | axios.put('/api/notices/1', { title })
    */
    public function update(Request $request, $id)
    {
        return response()->json([
            'message' => 'notice updated',
            'id' => $id,
            'input' => $request->all(),
        ]);
    }

    /*
    |--------------------------------------------------------------------------
    | DELETE /api/notices/{id}
    |--------------------------------------------------------------------------
    | 공지 삭제
    | Vue:
    | axios.delete('/api/notices/1')
    */
    public function destroy($id)
    {
        return response()->json([
            'message' => 'notice deleted',
            'id' => $id,
        ]);
    }
}