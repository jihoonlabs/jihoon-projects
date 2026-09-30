# Jira급 프로덕션 서비스를 위해 반드시 수정해야 할 인증 문제점 (ANALYSIS_LOGIN.md)

## ⚠️ 취약점 및 필수 수정 항목 (Critical Issues)

### 1. `login.ts`: 500/HTML 에러 시 앱 크래시 (치명적)
* **현상**: `response.ok` 검사 전에 `response.json()`을 바로 호출함.
* **문제**: 백엔드 서버 500 에러, Bad Gateway(502), 또는 점검 중 HTML 응답이 올 경우 JSON 파싱 실패(`SyntaxError`)로 예외 처리가 작동하지 않고 앱이 크래시됨.
* **조치**: `response.ok` 검사 후 파싱하거나, JSON Content-Type 확인 및 파싱 예외 처리 필요.

---

### 2. `fetchWithCsrf.ts`: 무조건적 CSRF 요청 & 토큰 재발급 부재 (성능/보안)
* **현상**: 모든 API 요청마다 `/sanctum/csrf-cookie`를 무조건 2번 호출함.
* **문제**:
  1. 모든 API 지연 시간(Latency)이 2배 증가함.
  2. 세션/CSRF 만료(419 Mismatch) 시 인터셉터를 통한 자동 토큰 재발급 및 재시도(Silent Retry) 로직이 없음.
* **조치**: 토큰 미보유 또는 419 응답 시에만 CSRF 토큰을 갱신하고 재시도하도록 래퍼 수정.

---

### 3. `middleware.ts`: 쿠키 키 불일치로 인한 검증 오작동 (보안 허점)
* **현상**: `middleware.ts`에서 `request.cookies.get('token')`을 검사하고 있음.
* **문제**: Laravel Sanctum 세션 인증 방식에서는 쿠키 이름이 `token`이 아니라 `laravel_session` 또는 `XSRF-TOKEN`으로 발행됩니다. 이로 인해 미들웨어가 쿠키를 정상 인식하지 못하거나 검증이 무력화될 위험이 있습니다.
* **조치**: Sanctum 세션 쿠키(`laravel_session` 또는 `XSRF-TOKEN`)를 검사하거나 백엔드 세션 검증 API와 연동하도록 미들웨어 수정.

---

### 4. `LoginForm.tsx`: `window.history.replaceState` 직접 조작
* **현상**: 쿼리 스트링 삭제를 위해 브라우저 DOM history를 직접 수정함.
* **문제**: Next.js App Router의 내부 라우터 상태와 비동기화 위험.
* **조치**: `router.replace('/login', { scroll: false })`로 변경.
