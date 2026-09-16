<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Auth\Events\PasswordReset;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Password;
use Illuminate\Support\Str;
use Illuminate\Validation\Rules\Password as PasswordRule;

class ResetPasswordController extends Controller
{
    public function __invoke(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'email' => ['required', 'string', 'email', 'max:255'],
            'token' => ['required', 'string'],
            'password' => [
                'required',
                'string',
                'confirmed',
                PasswordRule::min(8)
                    ->letters()
                    ->numbers(),
            ],
        ]);

        $user = User::query()
            ->where('email', $validated['email'])
            ->whereNotNull('password')
            ->whereNotNull('email_verified_at')
            ->where('status', 'active')
            ->first();

        if ($user === null) {
            return $this->invalidTokenResponse();
        }

        $status = Password::broker()->reset(
            [
                'email' => $validated['email'],
                'token' => $validated['token'],
                'password' => $validated['password'],
            ],
            function (User $user, string $password): void {
                $user->forceFill([
                    'password' => Hash::make($password),
                    'remember_token' => Str::random(60),
                ])->save();

                // 비밀번호 재설정 후 기존 로그인 세션을 모두 종료한다.
                DB::table('sessions')
                    ->where('user_id', $user->id)
                    ->delete();

                event(new PasswordReset($user));
            },
        );

        if ($status !== Password::PASSWORD_RESET) {
            return $this->invalidTokenResponse();
        }

        return response()->json([
            'message' => 'パスワードを再設定しました。新しいパスワードでログインしてください。',
        ]);
    }

    private function invalidTokenResponse(): JsonResponse
    {
        return response()->json([
            'message' => 'メールアドレスまたは再設定トークンが正しくないか、有効期限が切れています。',
        ], 422);
    }
}
