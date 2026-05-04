<?php

namespace App\Models;

// Laravel 기본 Model 클래스 (DB랑 연결해주는 역할)
use Illuminate\Database\Eloquent\Model;

class Notice extends Model
{
    /*
    | fillable (중요)
    | 사용자가 입력한 값을 DB에 저장할 때
    | 어떤 컬럼을 허용할지 정의하는 부분
    |
    | 없으면 Notice::create()가 막힐 수 있음
    |
    | 지금 우리가 만든 테이블:
    | title, content
    */
    protected $fillable = [
        'title',
        'content',
    ];
}