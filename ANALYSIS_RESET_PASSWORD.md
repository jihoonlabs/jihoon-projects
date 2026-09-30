# 비밀번호 재설정 (Reset Password) 핵심 리뷰 (ANALYSIS_RESET_PASSWORD.md)

## 1. 핵심 코드 흐름 (1줄 요약)
`forgot-password` ➔ `requestPasswordReset.ts` (`POST /api/auth/forgot-password`) ➔ 메일 발송 ➔ 링크 클릭 ➔ `reset-password` (`token`, `email`) ➔ `resetPassword.ts` (`POST /api/auth/reset-password`) ➔ 비밀번호 변경 완료

---

## 2. ⚠️ 필수 수정 항목 (Critical Issues)

### 1) API 공통: `response.json()` 비동기 파싱 순서 문제 (High Risk)
* **대상**: `requestPasswordReset.ts`, `resetPassword.ts`
* **문제**: `response.ok` 검사 전에 `response.json()`을 먼저 수행함. 백엔드 500 HTML 에러 발생 시 `SyntaxError`로 인해 폼이 비정상 종료(Crash)됨.

### 2) 사용자 열거 공격(User Enumeration Attack) 노출 (보안)
* **대상**: `requestPasswordReset.ts` / `ForgotPasswordForm.tsx`
* **문제**: 등록되지 않은 이메일 입력 시 `422` 에러("메일주소를 확인해주세요")를 반환하여, 공격자가 특정 이메일의 가입 여부를 계정 수집(Enumeration)할 수 있음.
* **조치**: 이메일 존재 여부와 상관없이 동일한 성공 메시지("입력하신 메일로 재설정 링크가 발송되었습니다.")를 반환하도록 정책 통일.

### 3) 비밀번호 성공 후 세션 무효화 & 리다이렉트 미처리 (UX/보안)
* **대상**: `ResetPasswordForm.tsx`
* **문제**: 비밀번호 변경 성공 후 단순 텍스트 메시지만 표시되고 폼이 닫힘. 
* **조치**: 성공 후 로그인 페이지(`/login`)로 자동으로 이동(`router.push`)시키거나 명확한 "로그인하러 가기" 버튼 안내 필요.
