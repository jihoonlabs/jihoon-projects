<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    /**
     * ログイン
     * Sanctum の SPA セッション認証を使用します。
     */
    public function login(Request $request)
    {
        $credentials = $request->validate([
            'email' => ['required', 'email'],
            'password' => ['required', 'string'],
        ]);

        if (! Auth::attempt($credentials)) {
            throw ValidationException::withMessages([
                'email' => ['メールアドレス及びパスワードが違います。'],
            ]);
        }

        // セッション固定攻撃対策
        $request->session()->regenerate();

        $user = $request->user();

        return response()->json([
            'message' => 'ログイン成功',
            'user' => [
                'id' => $user->id,
                'name' => $user->name,
                'email' => $user->email,
            ],
        ]);
    }

    /**
     * ログイン中のユーザ情報
     */
    public function user(Request $request)
    {
        return response()->json($request->user());
    }

    /**
     * ログアウト
     */
    public function logout(Request $request)
    {
        Auth::guard('web')->logout();

        // 現在のセッションを無効化
        $request->session()->invalidate();

        // CSRF トークンを再生成
        $request->session()->regenerateToken();

        return response()->json([
            'message' => 'ログアウトしました。',
        ]);
    }

    /**
     * 新規会員登録
     */
    public function register(Request $request)
    {
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'string', 'email', 'max:255', 'unique:users'],
            'password' => ['required', 'string', 'min:8'],
        ]);

        $user = User::create([
            'name' => $validated['name'],
            'email' => $validated['email'],
            'password' => Hash::make($validated['password']),
        ]);

        // 登録後、そのままログイン状態にする
        Auth::login($user);

        $request->session()->regenerate();

        return response()->json([
            'message' => '会員登録が完了しました。',
            'user' => [
                'id' => $user->id,
                'name' => $user->name,
                'email' => $user->email,
            ],
        ], 201);
    }
}