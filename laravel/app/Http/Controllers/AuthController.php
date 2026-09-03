<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    /**
     * login & Sanctum Bearer Token
     */
    public function login(Request $request)
    {
        $request->validate([
            'email' => ['required', 'email'],
            'password' => ['required', 'string'],
        ]);

        $user = User::where('email', $request->email)->first();

        // search password
        if (! $user || ! Hash::check($request->password, $user->password)) {
            throw ValidationException::withMessages([
                'email' => ['メールアドレス及びパスワードが違います。'],
            ]);
        }

        // $user->tokens()->delete();

        // New Bearer Token
        $token = $user->createToken('auth_token')->plainTextToken;

        return response()->json([
            'message' => 'ログイン成功',
            'access_token' => $token,
            'token_type' => 'Bearer',
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
        // Delete Bearer Token
        $request->user()->currentAccessToken()->delete();

        return response()->json([
            'message' => 'ログアウトしました。',
        ]);
    }
}