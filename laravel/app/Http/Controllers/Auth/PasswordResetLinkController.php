<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Password;

class PasswordResetLinkController extends Controller
{
    public function __invoke(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'email' => ['required', 'string', 'email', 'max:255'],
        ]);

        $user = User::query()
            ->where('email', $validated['email'])
            ->whereNotNull('password')
            ->whereNotNull('email_verified_at')
            ->where('status', 'active')
            ->first();

        if ($user !== null) {
            $token = Password::broker()->createToken($user);

            $user->sendPasswordResetNotification($token);
        }

        // 계정의 존재 여부와 상태를 외부 응답으로 노출하지 않는다.
        return response()->json([
            'message' => '入力されたメールアドレスが登録されている場合、パスワード再設定メールを送信しました。',
        ]);
    }
}
