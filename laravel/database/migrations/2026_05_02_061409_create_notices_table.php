<?php

// Migration 관련 클래스 import
use Illuminate\Database\Migrations\Migration;

// 테이블 구조 정의할 때 사용하는 클래스
use Illuminate\Database\Schema\Blueprint;

// DB 스키마(테이블 생성/삭제)를 다루는 클래스
use Illuminate\Support\Facades\Schema;

/*
| Migration
| DB table (create & update)
| 실행 시 DB 구조를 변경
| Migration를 상속받은 이름 없는 클랙스를 만듬
*/
return new class extends Migration
{
    /**
     * Run the migrations.
     *
     * "DB에 적용"할 때 실행됨
     * php artisan migrate 실행 시
     * DB에 notices table을 생성
     * 보이드 이므로 아무것도 리턴 안함
     */
    public function up(): void
    {
        /*
        | DB에 notices table create
        | 테이블 안에 칼럼(스키마) 정의
        */
        Schema::create('notices', function (Blueprint $table) {

            /*
            | id 컬럼 생성 (자동 증가 숫자)
            | SQL의 경우 id BIGINT AUTO_INCREMENT PRIMARY KEY
            */
            $table->id();

            /*
            | title 문자열 컬럼 생성
            | VARCHAR(255) 타입
            */
            $table->string('title');

            /*
            | content 컬럼
            | TEXT 타입
            | nullable() = 값 없어도 됨
            */
            $table->text('content')->nullable();

            /*
            | timestamps
            | 밑의 2개 칼럼 자동 생성
            | created_at → 생성 시간
            | updated_at → 수정 시간
            |
            | Laravel이 자동으로 관리
            */
            $table->timestamps();
        });
    }

    /**
     * 되돌릴때 실행
     * php artisan migrate:rollback
     */
    public function down(): void
    {
        /*
        |--------------------------------------------------------------------------
        | notices 테이블 삭제
        |--------------------------------------------------------------------------
        | 존재하면 삭제
        */
        Schema::dropIfExists('notices');
    }
};