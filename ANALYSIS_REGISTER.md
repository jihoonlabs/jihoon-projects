# 회원가입(Register) & 이메일 인증 핵심 리뷰 (ANALYSIS_REGISTER.md)

## 1. 핵심 코드 흐름 (1줄 요약)
`register/page.tsx` (서버) ➔ `RegisterForm.tsx` (입력/유효성검사) ➔ `register.ts` (API 호출) ➔ `fetchWithCsrf.ts` ➔ `Laravel` (`POST /api/auth/register` & 메일 발송) ➔ `/login?registered=1` 리다이렉트

---

## 2. ⚠️ 필수 수정 항목 (Critical Issues)

### 1) `register.ts`: `response.json()` 비동기 파싱 순서 문제 (High Risk)
* **현상**: `if (!response.ok)` 검사 전에 `const data = await response.json()`을 먼저 수행함.
* **문제**: 백엔드가 500(Internal Server Error), 502(Bad Gateway) 등 HTML 응답을 돌려줄 때 `SyntaxError`가 발생하여 캡처되지 않고 회원가입 폼이 비정상 종료(Crash)됨.
* **조치**: `response.ok` 상태 검사 후 파싱하거나 `try-catch` 파싱 예외 처리 필요.

### 2) `register.ts`: 422 서버 유효성 에러 단일 바인딩 제한
* **현상**: 백엔드에서 이름/이메일/비밀번호 다중 오류가 내려와도 `data.errors?.email?.[0] ?? ...`로 단 1개만 `serverError`에 노출함.
* **문제**: 사용자가 어떤 필드(이름인지, 비밀번호 규칙인지)가 틀렸는지 개별 필드별로 피드백을 받지 못함.
* **조치**: 개별 필드 에러 객체(`errors`)에 서버 에러 메시지를 맵핑하도록 수정.

### 3) 소셜 회원가입 CSRF State 미검증 (보안)
* **현상**: `window.location.href = '${API_URL}/api/auth/${provider}/redirect'`로 직접 이동.
* **문제**: OAuth 2.0 흐름 시 CSRF 방지용 `state` 토큰을 검증하지 않아 소셜 회원가입/로그인 계정 탈취 위험이 존재함.
