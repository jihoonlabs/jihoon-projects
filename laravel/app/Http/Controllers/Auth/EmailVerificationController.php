<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Support\FrontendUrl;
use Illuminate\Auth\Events\Verified;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class EmailVerificationController extends Controller
{
    /**
     * 署名付きURLからメール認証を完了する
     */
    public function __invoke(
        string $id,
        string $hash,
        Request $request,
    ): RedirectResponse {
        $user = User::findOrFail($id);

        abort_unless(
            hash_equals(
                $hash,
                sha1($user->getEmailForVerification()),
            ),
            403,
        );

        if (! $user->hasVerifiedEmail()) {
            $user->markEmailAsVerified();

            event(new Verified($user));
        }

        // clientは署名対象のため改ざんできない。未知の値は既定へ戻す。
        return redirect(
            FrontendUrl::forClient($request->query('client')).'/login?verified=1'
        );
    }
}
