# 勤怠管理 Epic

## 현재 상태

- 작업 브랜치: `feature/attendance` (`main`에서 분기, Ticket Epic과 독립).
- Laravel: 본인용 출근·퇴근·오늘 상태·기록 목록 API와 DB 저장 구현.
- React: `/attendance` 화면, Ticket·勤怠管理 메뉴, 상태별 버튼 비활성화, 기록 목록 구현.
- 기존 Sanctum 세션 인증과 `fetchWithCsrf`를 재사용한다.

## 확정 정책

- 사용자별 일본 날짜 기준 하루 한 번 출근하고 한 번 퇴근한다.
- 시각은 UTC로 저장하며 표시와 근무일 판정에는 `Asia/Tokyo`를 사용한다.
- 자정을 넘긴 퇴근도 출근 날짜의 기록을 마감한다. 미완료 기록이 있으면 새 출근을 차단한다.
- 근무시간은 퇴근시각에서 출근시각을 뺀 경과시간이며, 완료 기록에 분 단위로 표시한다. 휴게시간은 제외하지 않는다.
- 중복 출근·출근 없는 퇴근·재퇴근은 409로 차단한다. 요청의 `user_id`를 사용하지 않고 인증된 사용자를 사용한다.
- 휴게시간·기록 수정·관리자 기능은 후속 Epic 범위다.

## API와 DB

- `attendance_records`: `id`, `user_id`, `work_date`, `clock_in_at`, nullable `clock_out_at`, timestamps. `(user_id, work_date)` 고유 제약.
- `GET /api/attendance/today`: 일본 날짜, 상태(`not_started`/`working`/`finished`), 관련 기록.
- `GET /api/attendance?page=N`: 본인 기록을 근무일 역순으로 페이지당 30개.
- `POST /api/attendance/clock-in`, `POST /api/attendance/clock-out`: 서버 시각으로 상태 전이.
- 모든 경로에 `auth:sanctum`, `active.user`를 적용한다. 향후 관리자 조회는 별도 권한과 경로로 추가한다.

## 검증 및 남은 작업

- Laravel 전체 61개 테스트, React 전체 51개 테스트, TypeScript, ESLint, Pint, Next.js 빌드 통과.
- 임시 SQLite DB에 전체 마이그레이션 적용 확인.
- 실제 브라우저에서 로그인 후 CSRF 쿠키·세션과 출퇴근 버튼, 새로고침, 날짜 변경 및 자정 경계 표시를 확인해야 한다.
- 현재 `composer.lock`은 PHP 8.4 이상을 요구하는 패키지를 포함한다. 이 작업 환경에서는 PHP 8.3에 플랫폼 검사만 우회해 의존성을 설치하고 테스트했다. 실제 사용 환경에서는 잠금 파일과 일치하는 PHP 버전으로 재검증한다.
