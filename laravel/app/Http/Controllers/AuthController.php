<?php

namespace App\Http\Controllers;

use App\Models\SocialAccount;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;
use Illuminate\Support\Facades\DB;
use Laravel\Socialite\Facades\Socialite;

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

    /**
     * Google の認証画面へリダイレクト
     */
    public function googleRedirect()
    {
        return Socialite::driver('google')->redirect();
    }

    /**
     * Google 認証後のコールバック
     */
    public function googleCallback(Request $request)
    {
        $googleUser = Socialite::driver('google')->user();

        $socialAccount = SocialAccount::where('provider', 'google')
            ->where('provider_user_id', $googleUser->getId())
            ->first();

        if ($socialAccount) {
            Auth::login($socialAccount->user);
            $request->session()->regenerate();

            return redirect(
                config('services.frontend.url') . '/tickets'
            );
        }

        $email = $googleUser->getEmail();

        if (! $email) {
            return redirect(
                config('services.frontend.url') . '/login?error=google_email_missing'
            );
        }

        $emailVerified = (bool) ($googleUser->user['email_verified'] ?? false);

        if (! $emailVerified) {
            return redirect(
                config('services.frontend.url') . '/login?error=google_email_unverified'
            );
        }

        $user = DB::transaction(function () use ($googleUser, $email) {
            $user = User::where('email', $email)->first();

            if (! $user) {
                $user = User::create([
                    'name' => $googleUser->getName() ?? 'Google User',
                    'email' => $email,
                    'password' => null,
                ]);

                // Googleが確認済みのメールアドレスのみ認証済みとして扱う
                $user->email_verified_at = now();
                $user->save();
            } elseif (! $user->email_verified_at) {
                // Googleがメール所有を確認したため、既存ユーザーも認証済みにする
                $user->email_verified_at = now();
                $user->save();
            }

            SocialAccount::create([
                'user_id' => $user->id,
                'provider' => 'google',
                'provider_user_id' => $googleUser->getId(),
                'provider_email' => $email,
            ]);

            return $user;
        });

        Auth::login($user);
        $request->session()->regenerate();

        return redirect(
            config('services.frontend.url') . '/tickets'
        );
    }

    /**
     * LINE の認証画面へリダイレクト
     */
    public function lineRedirect()
    {
        return Socialite::driver('line')->redirect();
    }

    /**
     * LINE 認証後のコールバック
     */
    public function lineCallback(Request $request)
    {
        $lineUser = Socialite::driver('line')->user();

        $socialAccount = SocialAccount::where('provider', 'line')
            ->where('provider_user_id', $lineUser->getId())
            ->first();

        if ($socialAccount) {
            Auth::login($socialAccount->user);
            $request->session()->regenerate();

            return redirect(
                config('services.frontend.url') . '/tickets'
            );
        }

        $email = $lineUser->getEmail();
        
    }

}