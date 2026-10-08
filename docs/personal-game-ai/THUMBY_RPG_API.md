# 일반 Thumby 입력·저장 API 확장 Child

브랜치: feature/personal-game-ai-thumby-rpg-api
기반: 2fc67415a9d8adda97b15485da382735f755d43d

## 책임·계약
기존 generation_profile=thumby를 유지하고 target 설정의 thumby_features로 controls/save_data를 개별 선택한다. 생략 시 기존 좌우 pressed와 표시 API만 허용한다. controls는 여섯 버튼의 pressed/justPressed, save_data는 setName/setItem/getItem/hasItem/save를 허용한다. 알 수 없는 기능·중복·다른 프로필의 기능 선택은 거부한다. Color·별칭 import·순수 규칙의 thumby import 제한은 유지한다.

thumby_capabilities.py가 허용 API·72x40 흑백 제약·CPython fake 틀을 제공한다. 설계·엔트리 구현·테스트 프롬프트에 설정된 기능을 전달한다. 확장 테스트 프롬프트는 대상 import 이전 fake 주입, 유한 helper 호출, 실패·손상 테스트를 지시한다. production_request binding에 선택 기능을 기록하고 잘못된 기능 설정을 차단한다. 기존 target.json은 변경하지 않는다.

AST 검사는 직접 thumby 속성의 미허용/깊은 접근과 CPython 최상위 직접 saveData 호출을 차단한다. 간접 호출·동적 별칭·저장 값/실패 처리의 의미를 모두 증명하는 보안 경계는 아니다. CPython import 안전성은 실제 생성 테스트로 추가 확인한다. saveData의 원자적 쓰기·전원 중단 안전성을 보장하지 않는다.

공식 근거(2026-10-08 확인): https://thumby.us/API/Buttons/ , https://thumby.us/API/Save-Files/ , https://thumby.us/API/Graphics/ . 공식 API 설명은 실행/성능 측정과 구분한다.

## 검증·현재 상태
관련 98개 검사 통과(기존 프로필 38, 확장 10, 요청 연결 10, 기존 기획/조사/선택/명세/bridge 40). 기본 제한 보존·기능 독립 선택·잘못된 설정·직접 import 저장 차단·fake 저장 성공/실패·요청 binding을 확인했다. Python 3.12 실행과 3.9 문법 확인.
실제 Ollama·Docker·실기 미검증. RPG 게임 코드 생성/플레이, 자동 경험 검색·재사용·모델 학습은 미완료다. 다음은 집의 승인 명세를 새 게임 전용 checkout/target과 대조해 실제 설계 생성부터 진행하는 작업이다. 집의 dirty·승인·ThumbyDodge 결과를 원격 완료로 취급하지 않는다.

## 실제 설계 실패 후 수정
집 Ollama가 세 번 모두 단일 규칙 파일을 반환하고 ThumbyGrowth.py를 누락했다. 일반 module.py 예시 뒤에 실제 폴더명 엔트리와 규칙 파일의 두 파일 예시, 명시 상태/입력, 규칙의 기기 I/O 금지, 전체 R ID 목록을 추가한다. 일반 프로필/샌드박스의 JSON 계약은 유지한다. 승인 명세·기존 출력·digest는 변경하지 않는다. 단일 파일 응답 거부 후 재시도 프롬프트에도 대상 구조가 전달되는 검사를 추가했다. 관련 전체 120개 검사 통과. 이는 fake 모델 검증이며 실제 Ollama 재시도 성공은 집에서 확인해야 한다.
