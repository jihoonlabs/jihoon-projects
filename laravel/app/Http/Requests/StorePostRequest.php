<?php

namespace App\Http\Requests;

use Illuminate\Contracts\Validation\ValidationRule;
use Illuminate\Foundation\Http\FormRequest;

/**
 * 게시글(Post) 생성 요청(Request)을 검증하는 클래스
 *
 * Controller까지 요청이 전달되기 전에
 * 이 클래스에서 먼저 입력값을 검사한다.
 */

class StorePostRequest extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     * 현재 사용자가 이 요청을 실행할 권한이 있는지 확인한다.
     */
    public function authorize(): bool
    {
        return true;
    }

    /**
     * Get the validation rules that apply to the request.
     *
     * 게시글 생성 시 입력값 검증 규칙
     * @return array<string, ValidationRule|array<mixed>|string>
     */
    public function rules(): array
    {
        return [
            'content' => ['required', 'string'],
            'image_url' => ['nullable', 'string'],
        ];
    }
}
