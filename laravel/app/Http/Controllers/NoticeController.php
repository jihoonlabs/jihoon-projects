<?php

/*
| namespace
| PHP가 NoticeController 클래스를 App\Http\Controllers\NoticeController 라는 이름으로 찾을 수 있게 하는 선언
|
*/
namespace App\Http\Controllers;

/*
| Request(post/put)
| ex:
| axios.post('/api/notices', {
|   title: 'Title',
|   content: ''
| })
|
*/
use Illuminate\Http\Request;

/*
| Notice Model은 DB의 notices 테이블과 연결
|
| ex)
| Notice::all() -> notices 테이블의 모든 row를 가져옴
|
| Notice::create([...])
|   notices 테이블에 새 데이터를 저장
*/
use App\Models\Notice;

/*
| Route::get('/notices', [NoticeController::class, 'index']);
|
| GET /api/notices
| NoticeController 클래스의 index() 함수를 실행
*/
class NoticeController extends Controller
{
    /*
    | index()
    |
    | URL: GET /api/notices
    |
    | axios.get('/api/notices')
    |
    | 처리 흐름:
    | 1. Notice::all() 실행
    | 2. DB의 notices 테이블에서 모든 row를 가져옴
    | 3. JSON 형태로 프론트에 반환
    */
    public function index()
    {
        return response()->json([
            /*
            | message
            */
            'message' => 'notice list',

            /*
            | data
            |
            | Notice::all()
            |
            | SQL:
            | SELECT * FROM notices;
            */
            'data' => Notice::all(),
        ]);
    }

    /*
    | show($id)
    |
    | URL: GET /api/notices/{id}
    |
    | GET /api/notices/1
    |
    | Laravel이 URL의 {id=1}을 $id 변수에 넣어준다.
    |
    */
    public function show($id)
    {
        /*
        | Notice::findOrFail($id)
        | id에 해당하는 공지를 DB에서 찾음
        | 없으면 404 응답을 반환
        */
        $notice = Notice::findOrFail($id);

        return response()->json([
            'message' => 'notice detail',
            'data' => $notice,
        ]);
    }

    /*
    | store(Request $request)
    |
    | URL: POST /api/notices
    |
    | axios.post('/api/notices', {
    |   title: '1st',
    |   content: 'test'
    | })
    */
    public function store(Request $request)
    {
        /*
        | Notice::create()
        | ex: created_at, updated_at은 자동 생성
        | SQL:
        | INSERT INTO notices (title, content, created_at, updated_at)
        | VALUES (...);
        |
        */
        $notice = Notice::create([
            'title' => $request->title,
            'content' => $request->content,
        ]);

        /*
        | JSON 응답 반환
        | 201 = HTTP status code
        |
        | 201 Created
        */
        return response()->json($notice, 201);
    }

    /*
    | update(Request $request, $id)
    | URL: PUT /api/notices/{id}
    |
    | PUT /api/notices/1
    |
    | axios.put('/api/notices/1', {
    |   title: 'update 1st',
    |   content: 'update test'
    | })
    */
    public function update(Request $request, $id)
    {
        $notice = Notice::findOrFail($id);

        $notice->update([
            /*
            | $notice->update([...])
            | 찾은 공지 row의 title/content를 수정
            | updated_at은 자동 갱신
            */
            'title' => $request->title,
            'content' => $request->content,
        ]);

        return response()->json([
            'message' => 'notice updated',
            'data' => $notice,
        ]);
    }

    /*
    | destroy($id)
    |
    | URL: DELETE /api/notices/{id}
    |
    | DELETE /api/notices/1
    */
    public function destroy($id)
    {
        $notice = Notice::findOrFail($id);

        $notice->delete();

        return response()->json([
            'message' => 'notice deleted',
            'id' => $id,
        ]);
    }
}