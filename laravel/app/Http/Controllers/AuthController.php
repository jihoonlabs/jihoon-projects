<?php

namespace App\Http\Controllers;

use App\Models\SocialAccount;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;
use Illuminate\Validation\Rules\Password;
use Laravel\Socialite\Facades\Socialite;
use Throwable;

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

        if (! Auth::attempt([
            ...$credentials,
            'status' => 'active',
        ])) {
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
            'password' => [
                'required',
                'string',
                Password::min(8)
                    ->letters()
                    ->numbers(),
            ],
        ]);

        $user = User::create([
            'name' => $validated['name'],
            'email' => $validated['email'],
            'password' => $validated['password'],
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
     * ソーシャルログインの認証画面へリダイレクト
     */
   
    public function socialRedirect(string $provider)
    {
        $this->ensureSupportedProvider($provider);

        return Socialite::driver($provider)->redirect();
    }

    /**
     * ソーシャルログイン認証後のコールバック
     */
  
    public function socialCallback(string $provider, Request $request)
    {
        $this->ensureSupportedProvider($provider);

        try {
            $providerUser = Socialite::driver($provider)->user();
        } catch (Throwable) {
            return redirect(
                config('services.frontend.url')
                    . "/login?error=social_login_failed&provider={$provider}"
            );
        }

        $socialAccount = SocialAccount::where('provider', $provider)
            ->where('provider_user_id', $providerUser->getId())
            ->first();

        if ($socialAccount) {
            if ($socialAccount->user->status !== 'active') {
                return redirect(
                    config('services.frontend.url')
                        . "/login?error=account_unavailable&provider={$provider}"
                );
            }

            Auth::login($socialAccount->user);
            $request->session()->regenerate();

            return redirect(
                config('services.frontend.url') . '/tickets'
            );
        }

        $email = $providerUser->getEmail();

        $user = DB::transaction(function () use (
            $provider,
            $providerUser,
            $email
        ) {
            // メールアドレスでは既存ユーザーと自動連携しない
            $user = User::create([
                'name' => $providerUser->getName()
                    ?? ucfirst($provider) . ' User',
                'email' => null,
                'password' => null,
            ]);

            SocialAccount::create([
                'user_id' => $user->id,
                'provider' => $provider,
                'provider_user_id' => $providerUser->getId(),
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
     * 対応している認証プロバイダーのみ許可
     */
   
    private function ensureSupportedProvider(string $provider): void
    {
        abort_unless(
            in_array($provider, ['google', 'line'], true),
            404
        );
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