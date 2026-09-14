# 인증 프로젝트 진행 기준

최종 갱신: 2026-09-14  
현재 브랜치: `feature/auth-login`  
상태: 일반 로그인과 Google·LINE 소셜 로그인 구현 완료  
테스트: 30 passed, 130 assertions

## 1. 프로젝트 목표

Next.js App Router 프런트엔드와 Laravel 백엔드로 실제 서비스에 재사용할 수 있는 인증 기반을 만든다.

핵심 기준:

- Laravel Sanctum 기반 SPA 세션 인증
- Next.js와 Laravel 분리 구성
- 일반 이메일 로그인과 소셜 로그인 지원
- 계정 상태에 따른 접근 제어
- 인증 정책을 Feature Test로 고정
- 공개 GitHub 포트폴리오로 제시할 수 있는 품질

## 2. 전체 진행 순서와 현재 위치

| 단계 | 작업 | 상태 |
| --- | --- | --- |
| 1 | Laravel 회원가입·로그인·로그아웃 | 완료 |
| 2 | Sanctum 세션 인증과 `/api/auth/me` | 완료 |
| 3 | Next.js 세션 복원과 보호 페이지 | 완료 |
| 4 | 계정 상태(`active`, `suspended`) 처리 | 완료 |
| 5 | Google Socialite 로그인 | 완료 |
| 6 | 로그인 보안 테스트와 Rate Limit | 완료 |
| 7 | LINE Socialite 로그인 | 완료 |
| 8 | 인증 코드 전체 파일별 리뷰 | **다음 단계** |
| 9 | README와 실행·환경설정 문서 | 미완료 |
| 10 | 최종 브라우저 회귀 테스트와 공개 준비 | 미완료 |

현재 위치는 인증 구현을 끝내고 전체 코드 리뷰를 시작하기 직전이다.

## 3. 완료된 기능

### 일반 인증

- 올바른 이메일과 비밀번호로 로그인
- 잘못된 로그인 정보 거절
- 신규 회원가입
- 중복 이메일 거절
- 비밀번호 최소 길이와 영문·숫자 정책
- 로그인 후 현재 사용자 조회
- 로그아웃과 세션 종료
- 비로그인 사용자의 보호 API 접근 시 `401`
- 로그인과 회원가입 Rate Limit

### 계정 상태

- 신규 사용자의 기본 상태는 `active`
- `suspended` 사용자의 일반 로그인 차단
- 로그인된 사용자가 정지된 경우 보호 API 접근 시 `403`
- 정지 사용자 발견 시 인증 세션 무효화
- 이후 요청은 미인증 상태로 `401`
- `active.user` 미들웨어를 보호 API에 공통 적용

### 소셜 로그인 정책

- Google과 LINE을 공통 Socialite callback으로 처리
- `provider`와 `provider_user_id`로 소셜 계정을 식별
- 동일 이메일의 기존 User와 자동 연결하지 않음
- provider가 제공한 이메일은 `provider_email`에 참고 정보로 저장
- 신규 소셜 User의 `email`과 `password`는 `null` 허용
- 기존 SocialAccount가 있으면 연결된 기존 User로 로그인
- 정지된 소셜 계정은 로그인 차단
- User와 SocialAccount 생성을 DB 트랜잭션으로 처리
- 로그인 후 세션 재생성 및 `/tickets` 이동
- OAuth 실패 시 내부 예외를 기록하고 로그인 화면으로 이동

### Google 로그인

- Google Developers 설정 완료
- 실제 브라우저 로그인 확인 완료
- 신규 Google 사용자 로그인 확인
- 기존 SocialAccount 로그인 처리
- 프런트엔드 오류 표시 처리

### LINE 로그인

- LINE Developers Provider와 LINE Login 채널 생성
- Callback URL 등록
- LINE Socialite provider 설치 및 등록
- Laravel 환경변수 연결
- 이메일이 없는 LINE 사용자 생성 지원
- 실제 브라우저 로그인 확인
- `/tickets` 이동 및 세션 유지 확인
- 재로그인 시 SocialAccount 중복 생성 없음

### 프런트엔드

- Next.js App Router와 TypeScript
- CSS Modules 사용
- Feature-First 구조 적용
- 일반·Google·LINE 로그인 UI
- `/me`를 이용한 세션 복원
- 로그아웃
- 보호 페이지 접근 제어
- 소셜 로그인 오류 메시지 표시

## 4. 테스트 기준

- 일반 로그인·회원가입·로그아웃·`/me`
- 정지 사용자 접근 차단과 세션 종료
- 로그인·회원가입 Rate Limit
- Google 신규 소셜 사용자
- 이메일 없는 LINE 신규 사용자
- 기존 SocialAccount 재로그인
- 동일 이메일 사용자와 자동 연결하지 않는 정책
- 지원하지 않는 provider의 `404`
- OAuth 실패 처리
- 정지된 소셜 계정 차단
- 전체 테스트: 30 passed
- 전체 assertions: 130

Socialite 자동 테스트는 외부 Google·LINE 서버에 접속하는 E2E 테스트가 아니다. provider 사용자 응답을 mock하여 callback 정책과 DB·인증 동작을 검증한다. 실제 OAuth 동작은 브라우저에서 별도로 확인한다.

## 5. 다음 작업: 인증 전체 리뷰

일반 로그인과 Google·LINE 소셜 로그인 구현은 완료됐다.

다음 단계에서는 파일별로 다음을 확인한다.

- 파일이 필요한 이유
- 현재 폴더에 위치하는 이유
- 책임 분리가 적절한지
- 인증·보안 정책과 테스트가 일치하는지
- 오류 처리와 테스트 가능성이 충분한지
- 중복 코드와 불필요한 코드가 없는지

CSS와 시각 디자인은 이번 리뷰의 우선 대상에서 제외한다.

## 6. 리뷰 이후 남은 작업

- README에 프로젝트 목적과 기술 구성 작성
- 로컬 실행 방법 작성
- Next.js와 Laravel 환경변수 예시 작성
- Google과 LINE OAuth 설정 방법 작성
- 인증 흐름과 소셜 계정 연결 정책 설명
- 테스트 실행 방법 작성
- 비밀키가 Git에 포함되지 않았는지 최종 확인
- 전체 브라우저 회귀 테스트
- `main` 병합
- 레바테크 포트폴리오에 GitHub 등록

## 7. 중복 작업 방지 규칙

1. 작업 시작 전에 이 문서의 현재 위치를 확인한다.
2. 완료 항목은 오류가 재현되거나 정책이 바뀌지 않는 한 다시 구현하지 않는다.
3. 자동 테스트와 실제 브라우저 확인을 구분한다.
4. 정책이 변경되면 코드, Feature Test, 이 문서를 함께 갱신한다.
5. 작업 종료 시 완료 기능, 테스트 결과, 커밋, 다음 단계를 확인한다.
6. 전체 테스트 통과와 원격 저장소 push까지 끝난 지점을 체크포인트로 삼는다.

## 8. 다음 세션 시작 기준

> 일반 로그인과 Google·LINE 소셜 로그인 구현 및 실제 브라우저 확인이 완료됐다. 전체 테스트는 30개, 130 assertions가 통과했다. 다음 작업은 인증 코드를 파일별로 리뷰하고 README를 정리하는 것이다.