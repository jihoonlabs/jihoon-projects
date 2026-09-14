# 인증 포트폴리오 프로젝트 진행 기준

최종 갱신: 2026-09-14  
현재 브랜치: `feature/auth-login`  
현재 체크포인트 커밋: `2029e02`  
상태: 전체 테스트 통과, 원격 저장소 push 완료, working tree clean

## 1. 프로젝트 목표

Next.js App Router 프런트엔드와 Laravel 백엔드로 실제 서비스에 재사용할 수 있는 인증 기반을 만든다. 단순 데모가 아니라 공개 GitHub 포트폴리오에 올릴 수 있는 수준을 목표로 한다.

핵심 기준:

- Laravel Sanctum 기반 세션 인증
- Next.js와 Laravel의 분리 구성
- 일반 이메일 로그인과 소셜 로그인 지원
- 계정 상태에 따른 접근 제어
- 인증 정책을 Feature Test로 고정
- 나중에 큰 구조 변경 없이 다른 서비스에 재사용 가능

## 2. 전체 진행 순서와 현재 위치

| 단계 | 작업 | 상태 |
| --- | --- | --- |
| 1 | Laravel 기본 회원가입·로그인·로그아웃 | 완료 |
| 2 | Sanctum 세션 인증과 `/api/auth/me` | 완료 |
| 3 | Next.js 세션 복원과 보호 페이지 | 완료 |
| 4 | 계정 상태(`active`, `suspended`) 처리 | 완료 |
| 5 | Google Socialite 로그인 | 완료 |
| 6 | 인증 보안 테스트와 Rate Limit | 완료 |
| 7 | LINE Socialite 로그인 | **다음 구현 단계** |
| 8 | 인증 코드 전체 파일별 리뷰·정리 | LINE 완료 후 |
| 9 | README와 실행·환경설정 문서 | 미완료 |
| 10 | 최종 브라우저 회귀 테스트와 공개 준비 | 미완료 |

현재 위치는 **Google 인증까지 닫고 LINE 로그인을 시작하기 직전**이다.

## 3. 완료된 기능

### 일반 인증

- 올바른 이메일과 비밀번호로 로그인
- 잘못된 비밀번호 거절
- 신규 회원가입
- 중복 이메일 거절
- 비밀번호 최소 길이 및 영문·숫자 정책
- 로그인 후 현재 사용자 조회(`/api/auth/me`)
- 로그아웃 및 세션 종료
- 비로그인 사용자의 보호 API 접근 시 `401`
- 로그인 및 회원가입 Rate Limit

### 계정 상태

- 기본 신규 사용자의 상태는 `active`
- `suspended` 사용자의 일반 로그인 차단
- 이미 로그인된 사용자가 정지된 경우 보호 API 접근 시 `403`
- 정지 사용자 발견 시 web 인증 세션 무효화 및 CSRF 토큰 재생성
- 이후 요청은 미인증 상태가 되어 `401`
- 공통 `active.user` 미들웨어로 보호 API에 적용

### Google 로그인

- Google OAuth 실제 브라우저 동작 확인
- 검증된 이메일만 허용
- Google에서 이메일이 없으면 `google_email_missing`으로 로그인 페이지 이동
- 이메일이 미인증이면 `google_email_unverified`로 로그인 페이지 이동
- 동일한 검증 이메일의 기존 User가 있으면 새 User를 만들지 않고 연결
- 신규 Google 사용자는 User와 SocialAccount 생성
- 기존 SocialAccount는 기존 User로 로그인
- User 생성과 SocialAccount 연결을 DB 트랜잭션으로 처리
- 로그인 후 세션 재생성 및 `/tickets` 이동
- 프런트엔드에서 Google 오류 쿼리를 일본어 메시지로 표시한 뒤 URL 정리

Google 관련 자동 테스트는 Google 서버에 실제 접속하는 E2E 테스트가 아니다. Socialite 사용자 응답을 mock하여 **우리 callback 정책과 DB·인증 동작**을 검증하는 Laravel Feature Test다.

### 프런트엔드

- Next.js App Router + TypeScript
- CSS Modules만 사용
- Feature-First 구조 적용
- 로그인 폼과 Google 오류 표시
- `/me`를 이용한 세션 복원
- 로그아웃
- 보호 페이지 접근 제어

## 4. 현재 테스트 기준

- Google callback 핵심 케이스 5개 통과
  - 검증된 신규 Google 사용자
  - 동일 이메일 기존 사용자 연결
  - 기존 SocialAccount 로그인
  - Google 이메일 없음
  - Google 이메일 미인증
- 일반 로그인·회원가입·로그아웃·`/me` 테스트 통과
- 정지 사용자 접근 및 세션 종료 테스트 통과
- 로그인·회원가입 Rate Limit 테스트 통과
- 2026-09-14 기준 전체 테스트 통과

## 5. 다음 작업: LINE 로그인

LINE은 Google 구현을 복사하는 작업이 아니라, 공통 정책은 유지하고 provider 차이만 분리해서 추가한다.

진행 순서:

1. 현재 LINE callback stub과 관련 route 확인
2. 사용할 Socialite LINE provider 패키지와 Laravel/PHP 호환성 확인
3. LINE Developers 채널 설정 및 환경변수 정의
4. LINE redirect와 callback 구현
5. `social_accounts`에 `provider_name = line`으로 연결
6. LINE이 제공하는 이메일의 존재 여부와 신뢰 정책 결정
7. 기존 User 연결·신규 User 생성·기존 SocialAccount 로그인 구현
8. DB 트랜잭션과 세션 재생성 적용
9. LINE 전용 Feature Test 작성
10. Next.js 로그인 버튼과 오류 메시지 연결
11. 실제 브라우저 로그인 확인

중요: LINE의 이메일 제공 조건은 Google과 다를 수 있으므로, 구현 전에 **이메일이 없을 때 계정을 어떻게 처리할지** 정책을 먼저 확정한다.

## 6. LINE 이후 남은 작업

### 인증 전체 리뷰

파일별로 다음 기준을 확인한다.

- 이 파일이 왜 필요한가
- 왜 현재 폴더에 위치하는가
- 책임이 지나치게 크거나 중복되지 않는가
- 인증·보안 정책이 코드와 테스트에 일치하는가
- 타입, 오류 처리, 테스트 가능성이 충분한가

CSS와 시각 디자인은 이 리뷰의 우선 대상에서 제외한다.

### 문서화와 공개 준비

- README에 프로젝트 목적과 기술 구성 작성
- 로컬 실행 방법 작성
- Next.js/Laravel 환경변수 예시 작성
- Google/LINE OAuth 설정 방법 작성
- 인증 흐름과 계정 연결 정책 설명
- 테스트 실행 방법 작성
- 비밀키와 실제 인증정보가 Git에 포함되지 않았는지 확인
- 최종 브라우저 회귀 테스트

## 7. 중복 작업 방지 규칙

1. 새로운 작업을 시작하기 전에 이 문서의 현재 위치를 먼저 확인한다.
2. 완료 항목은 문제가 재현되거나 요구사항이 바뀌지 않는 한 다시 구현하지 않는다.
3. 자동 테스트와 실제 브라우저 확인을 구분해서 기록한다.
4. 새 정책을 추가하면 구현뿐 아니라 해당 Feature Test와 이 문서를 함께 갱신한다.
5. 작업 종료 시 반드시 다음 네 가지를 기록한다.
   - 완료한 기능
   - 실행한 테스트와 결과
   - 마지막 커밋
   - 다음 한 단계
6. `git status`가 clean이고 push까지 끝난 지점을 공식 체크포인트로 삼는다.

## 8. 다음 세션 시작 문장

다음에는 아래 기준으로 시작한다.

> 인증 프로젝트는 `feature/auth-login`의 커밋 `2029e02`까지 저장되어 있고 전체 테스트가 통과했다. Google 인증은 완료됐으며, 다음 작업은 기존 LINE stub과 route를 확인하고 LINE 이메일 정책을 결정하는 것이다.

