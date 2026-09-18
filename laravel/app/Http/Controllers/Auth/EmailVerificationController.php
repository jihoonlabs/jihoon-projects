<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Auth\Events\Verified;
use Illuminate\Http\RedirectResponse;

class EmailVerificationController extends Controller
{
    /**
     * 署名付きURLからメール認証を完了する
     */
    public function __invoke(
        string $id,
        string $hash,
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

        return redirect(
            config('services.frontend.url').'/login?verified=1'
        );
    }
}
