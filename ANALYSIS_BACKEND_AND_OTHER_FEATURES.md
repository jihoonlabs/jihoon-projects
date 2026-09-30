# 백엔드 API 컨트롤러 & 기타 기능(Notices/Posts) 핵심 리뷰 (ANALYSIS_BACKEND_AND_OTHER_FEATURES.md)

## 1. 개요
본 문서는 Laravel 백엔드 API 컨트롤러(`TicketController`, `NoticeController`, `AuthController` 등)와 기타 보조 기능(`notices`, `posts`)에 대한 분석 및 프로덕션 관점의 핵심 지적 사항 정리 보고서입니다.

---

## 2. ⚠️ 백엔드 API & 컨트롤러 필수 개선 항목 (Critical Issues)

### 1) API 미들웨어 권한(Authorization/Policy) 미적용
* **대상**: `TicketController.php`, `NoticeController.php`
* **현상**: `store`, `updateStatus`, `destroy` 등에서 사용자 권한(Policy / Gate) 체크 없이 DB를 바로 수정함.
* **문제**: 로그인된 사용자라면 타인의 티켓이나 시스템 공지사항을 임의로 수정/삭제할 수 있는 권한 오남용 위험이 존재함.
* **조치**: Laravel Policy(`TicketPolicy`, `NoticePolicy`)를 추가하고 `$this->authorize('update', $ticket)` 적용 필요.

### 2) `NoticeController.php`: `Notice::all()` 전체 조회 성능 이슈
* **대상**: `NoticeController.php` (index 메서드)
* **현상**: 페이징 처리 없이 `Notice::all()`로 테이블의 모든 데이터를 한 번에 가져옴.
* **문제**: 데이터가 쌓이면 서버 메모리 고갈 및 응답 지연 발생.
* **조치**: `Notice::latest()->paginate(15)` 형태로 페이징 처리 적용.

### 3) 단일 프로젝트 중심의 `issue_key` 생성 구조 (`TicketController.php`)
* **현상**: `store` 메서드에서 `'TICK-' . $ticket->id` 형태로 issue_key를 하드코딩 생성함.
* **문제**: Jira와 같은 다중 프로젝트(Multi-Project / Multi-Tenant) 구조 확장 시 프로젝트별 식별자(예: `PROJ-1`, `FRONT-12`)를 유연하게 발행할 수 없음.
* **조치**: 프로젝트(`Project`) 모델 연동 후 프로젝트 키 기반의 일련번호 생성 로직으로 변경.
