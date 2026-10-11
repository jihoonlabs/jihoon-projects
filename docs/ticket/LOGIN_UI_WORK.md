# Login UI and Behavior

owner_repo: jihoonlabs/jihoon-projects
owner_branch: feature/ticket-login-ui
role: child
base_sha: cd6ada3aafdcdd6d2e561e1180880e44a77be271
status: ready_for_integration

## Responsibility

Keep the existing title/subtitle, card, routes and authentication contracts. Place the password toggle inside the input; align login/social buttons and Japanese divider, spacing, mobile layout and focus. Verify login success/failure/validation, Enter, duplicate submission, loading, server/network errors, redirect, session/logout and recovery/social links. Fix demonstrated login bugs with focused regression tests. No unrelated refactor, new authentication contract, Epic implementation/merge, push or asset deletion.

## Context and decisions

- Epic has adopted detail concurrency candidate 07b0f0088798f1180879c46dcdd2fc3443401370; current base is its adoption-record commit above. Existing feature/auth-login is an old ancestral checkpoint, not an ongoing Child for this responsibility.
- Gray password/social buttons have no CSS class or corresponding styles; the primary button is styled. Use the existing CSS Module and lucide-react Eye/EyeOff. No existing service logo asset was found; retain clear Google/LINE text and distinct service styling without invented logos or dependencies. Shared Button files are empty placeholders and remain untouched.
- Existing API uses Sanctum/CSRF and active/verified user checks. Preserve those checks and navigation to /tickets. Existing Epic app at localhost:3000/8000 stays running; Child uses a separate frontend/API and temporary SQLite with isolated session/cache/storage.

## Implementation and demonstrated bugs

- Password field wrapper reserves right padding for the existing Eye/EyeOff toggle (type=button, accessible name/pressed state). Main/Google/LINE buttons share height, radius, font/alignment and focus styles; service text/styles are distinct. Japanese divider, compact spacing and mobile wrapping retain the title/subtitle/card. No new dependency, logo drawing or component extraction.
- An in-flight ref blocks two submissions in the same render; loading disables relevant controls. Real Chrome found an unnamed busy submit button caused by its nested status element; an explicit derived accessible name fixes it.
- Non-JSON server errors, network errors and invalid successful user payloads now produce clear login errors without entering authenticated state or discarding input. Existing 403 verification and 429 messages are retained.
- A late initial /me response could erase a newer login. Store-snapshot/lifecycle guards prevent obsolete updates. Real delayed Laravel responses also exposed an old Set-Cookie overwriting a new session: cancel the pending restore before login/logout requests and on initializer cleanup. API routes, cookie authentication, CSRF, verification and active-user checks are unchanged.
- Existing shared Header falsely cleared client auth even when logout failed. It now reports the failure, retains state and permits retry. This Header is not currently mounted by the Ticket page; its UI behavior is tested in isolation, while actual logout/session invalidation is tested against Laravel. No new logout UI was added to Ticket.

## Verification results

- Initial focused regression tests reproduced stale-auth, malformed-success, HTML/network-error and failed-logout defects before their fixes. Real Chrome reproduced busy-button naming and delayed-cookie session loss before correction.
- Final React full suite: 25 files / 180 tests passed. TypeScript, ESLint, changed-file Prettier and final production build passed. Related Laravel Login/Register/SocialLogin/EmailVerification/CSRF: 32 tests / 151 assertions passed against isolated testing configuration.
- Actual Child frontend → Laravel → temporary SQLite: 7 grouped scenarios passed with no fabricated API responses. Desktop 1440×900 and mobile 375×812 / 320×568: controls remain within horizontal bounds, toggle is inside the input with text clearance, 3 action buttons share 44px height, keyboard focus and screenshots checked.
- Real 422 credentials, Enter/synchronous duplicate submission, loading, success → /tickets, reload session, logout → 401/login, temporary-DB 500, aborted transport/network retry, delayed original Laravel /me response, forgot/register navigation and both social start 302s verified. Expected original-response cancellation is not an authentication bypass.
- Browser harness failures from Next route-announcer selection and a leftover diagnostic timer were corrected; the final script completed successfully. These execution failures are distinct from the reproduced product bugs.
- Evidence/scripts/screenshots: `/private/tmp/ticket-login-ui-check-20261012/{browser-result.json,laravel-tests.xml,check.cjs,run.py,login-desktop.png,login-mobile.png}`. Preview remains running at http://127.0.0.1:3240/login, API 8140. Runtime env/storage/cache/session/SQLite are isolated. Credentials are local in a permission-600 file and are not committed or reported as plaintext.
- Original Epic remains at base_sha, with its existing 3000/8000 app, ai/, env and DB preserved. No reset/global seeding, push/merge or existing asset deletion. Final handoff SHA is owner_branch HEAD; only this Child is committed.

## Remaining boundaries

Google/LINE external authentication completion and callback-registration compatibility in the isolated port are unverified; only real start redirects were observed. No provider-console changes or external account authentication were performed. MySQL concurrency/row locks are unverified. Parent integration/adoption and Ticket V1 completion are separate responsibilities.

## Improvement note

Browser automation must scope error locators to the login card because Next.js also exposes a route-announcer alert. Remove diagnostic timers after races so completed checks cannot fail during teardown.
