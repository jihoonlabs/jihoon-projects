# 인증 프로젝트 체크포인트

최종 갱신: 2026-09-15
현재 브랜치: `feature/auth-login`  
기준 커밋: `152d8c0 feat: complete LINE social login`
현재 상태: 이메일 인증 기능 구현 중

## 1. 프로젝트 목표

Next.js App Router와 Laravel을 사용해 실제 서비스에 재사용할 수 있는 인증 기반을 만든다.

- Laravel Sanctum SPA 세션 인증
- 이메일·비밀번호 로그인
- Google·LINE 소셜 로그인
- 계정 상태에 따른 접근 제어
- 인증 정책을 Feature Test로 검증
- 공개 GitHub 포트폴리오 수준으로 문서화

## 2. 완료된 인증 기능

### 일반 인증

- 회원가입
- 로그인과 로그아웃
- `/api/auth/me`를 이용한 세션 복원
- 비로그인 사용자의 보호 API 접근 시 `401`
- 로그인과 회원가입 Rate Limit
- 비밀번호 최소 길이와 영문·숫자 정책

### 계정 상태

- 신규 사용자의 기본 상태는 `active`
- `suspended` 사용자의 로그인 차단
- 로그인 후 정지된 사용자의 보호 API 접근 시 `403`
- 정지 사용자 발견 시 인증 세션 무효화
- 이후 요청은 미인증 상태로 `401`
- `active.user` 미들웨어를 보호 API에 적용

### 소셜 로그인

- Google Socialite 로그인
- LINE Socialite 로그인
- Google·LINE 실제 브라우저 로그인 확인
- `provider`와 `provider_user_id`로 소셜 계정 식별
- 기존 SocialAccount 재로그인 시 중복 생성 방지
- 정지된 소셜 계정 로그인 차단
- OAuth 실패 처리 및 내부 예외 기록
- User와 SocialAccount 생성을 DB 트랜잭션으로 처리
- 로그인 후 세션 재생성과 `/tickets` 이동

## 3. 계정 연결 정책

사용자는 다음 세 가지 방법 중 하나를 선택해 로그인한다.

- 이메일과 비밀번호
- Google
- LINE

각 로그인 방식은 자동으로 서로 연결하지 않는다.

- 동일 이메일이어도 기존 User와 SocialAccount를 자동 연결하지 않음
- 소셜 provider의 이메일은 `provider_email`에 참고 정보로 저장
- 신규 소셜 User의 `email`과 `password`는 `null` 허용
- 로그인할 때는 가입 시 사용한 인증 방법을 사용

## 4. 이메일 인증 정책

이메일 회원가입은 인증 링크를 클릭해야 완료된다.

1. 이름·이메일·비밀번호 제출
2. User 생성
3. 인증메일 발송
4. 가입 직후에는 로그인하지 않음
5. 인증 전 이메일 로그인은 `403 email_not_verified`
6. 서명된 인증 링크로 이메일 소유권 확인
7. 인증 완료 후 로그인 화면으로 이동
8. 이메일과 비밀번호로 로그인

Google과 LINE 로그인에는 이 이메일 인증 절차를 적용하지 않는다.

## 5. 이메일 인증 구현 상태

### 완료

- `User` 모델에 `MustVerifyEmail` 적용
- 회원가입 시 `VerifyEmail` 알림 발송 로직 구현 및 Feature Test 확인
- 회원가입 직후 자동 로그인 제거
- 미인증 사용자의 이메일 로그인 차단
- 미인증 로그인 후 세션 제거
- 정상적인 서명 URL로 이메일 인증
- 인증 완료 후 `/login?verified=1`로 이동
- 이메일 해시가 다른 인증 링크 차단
- 만료된 서명 URL 차단
- 인증메일 재전송 API 구현
- 미등록 이메일에도 동일한 응답을 반환
- 계정 존재 여부 노출 방지
- 현재까지 추가한 이메일 인증 개별 Feature Test 통과

### 현재 작업

이미 인증된 사용자에게 인증메일을 다시 보내지 않는지 확인한다.

기대 결과:

- API 응답은 다른 재전송 요청과 동일한 `200`
- 실제 인증 알림은 발송하지 않음
- 가입 여부와 인증 여부를 외부 응답으로 노출하지 않음

## 6. 다음 작업 순서

1. 인증 완료 사용자의 재전송 방지 테스트
2. `EmailVerificationTest` 전체 실행
3. 인증메일 재전송 Rate Limit 테스트
4. 전체 Laravel 테스트 실행
5. Pint와 `git diff --check`
6. 개발 환경에서 실제 인증메일 URL 확인
7. Next.js 회원가입 완료 안내 추가
8. 로그인 화면의 `verified=1` 메시지 처리
9. 로그인 화면의 `email_not_verified` 오류 처리
10. 체크포인트와 테스트 결과 갱신
11. 커밋 및 push
12. 인증 코드 전체 리뷰
13. README와 공개 준비

## 7. 주요 관련 파일

### 모델과 컨트롤러

- `app/Models/User.php`
- `app/Http/Controllers/AuthController.php`
- `app/Http/Controllers/Auth/EmailVerificationController.php`
- `app/Http/Controllers/Auth/EmailVerificationNotificationController.php`

### 라우트

- `routes/api/auth.php`
- `routes/web.php`

### 테스트

- `tests/Feature/Auth/LoginTest.php`
- `tests/Feature/Auth/RegisterTest.php`
- `tests/Feature/Auth/SocialLoginTest.php`
- `tests/Feature/Auth/EmailVerificationTest.php`

## 8. 테스트 기준

자동 테스트에서는 실제 Google·LINE 서버나 메일 서버에 접속하지 않는다.

- Socialite 사용자 응답은 mock으로 처리
- 이메일 Notification은 fake로 처리
- 실제 OAuth 동작은 브라우저에서 별도로 확인
- 실제 인증메일 내용은 개발용 mail driver로 별도 확인

테스트 숫자는 이메일 인증 구현 완료 후 전체 테스트 결과로 갱신한다.

## 9. 작업 규칙

- 기능을 한 단계씩 구현하고 실행 결과를 확인한다.
- 구현 전에 요구사항과 보안 정책을 확정한다.
- 각 변경의 목적, 파일 위치, 처리 흐름을 확인한다.
- 구현 코드에는 필요한 테스트를 함께 추가한다.
- 테스트 실패가 예상된 실패인지 실제 오류인지 구분한다.
- 완료된 기능은 오류 재현이나 정책 변경이 없으면 다시 구현하지 않는다.
- 자동 테스트와 실제 브라우저 확인을 구분한다.
- 정책 변경 시 코드, 테스트, 체크포인트를 함께 갱신한다.
- 작업 종료 전에 전체 테스트, Pint, `git diff --check`를 실행한다.
- 전체 테스트 통과와 원격 저장소 push까지 끝난 지점을 공식 체크포인트로 삼는다.
- 프로젝트 공개 준비가 끝나면 이 임시 체크포인트 파일을 삭제한다.
- 로그인 기능을 완성한 뒤 인증 관련 파일을 하나씩 검토하고, 탐색을 위한 이정표와 정책·보안상의 이유가 필요한 위치에만 주석을 추가한다.

## 10. 다음 세션 시작 기준

> `feature/auth-login`에서 일반 로그인과 Google·LINE 로그인까지 완료했다. 현재 이메일 인증을 구현 중이며, 미인증 로그인 차단, 서명 링크 인증, 잘못된 해시와 만료 링크 차단, 인증메일 재전송, 계정 열거 방지까지 완료했다. 다음 작업은 인증 완료 사용자에게 인증메일을 재전송하지 않는 테스트부터 이어간다.