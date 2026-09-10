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
     * SanctumのSPAセッション認証を使用します。
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
            'user' => $this->formatUser($user),
        ]);
    }

    /**
     * ログイン中のユーザー情報を取得
     */
    public function user(Request $request)
    {
        return response()->json(
            $this->formatUser($request->user()),
        );
    }

    /**
     * ログアウト
     */
    public function logout(Request $request)
    {
        Auth::guard('web')->logout();

        // 現在のセッションを無効化
        $request->session()->invalidate();

        // CSRFトークンを再生成
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
            'user' => $this->formatUser($user),
        ], 201);
    }

    /**
     * フロントエンドで使用するユーザー形式に変換
     */
    private function formatUser(User $user): array
    {
        return [
            'id' => $user->id,
            'name' => $user->name,
            'email' => $user->email,
            'status' => $user->status,
            'createdAt' => $user->created_at?->toISOString(),
        ];
    }
}