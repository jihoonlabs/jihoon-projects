# 제작 명세 — MANUAL

축소안 선택 결과를 제작 명세로 묶고, 검토 후 그 명세에 대한 승인을 별도로 저장하는 CLI를 추가했다. 원래 기획과 검토 기록은 유지한다.

details.json에 scope, rules, controls, display_defaults, resource_budget, acceptance, unverified 일곱 항목을 넣는다. 값은 각각 문자열 목록이다. 화면 기본값·자원 예산은 실제 검증 전이면 후보 또는 미확인이라고 적는다.

저장소 루트에서 검토 파일 작성:

```sh
python ai/personal-game-ai/production_spec.py --brief chosen-brief.json --details details.json --output spec-review.json
```

spec-review.json을 읽고 내용이 맞으면 출력된 digest를 사용한다:

```sh
python ai/personal-game-ai/production_spec.py --record spec-review.json --approve 검토한_digest --output spec-approved.json
```

파일 내용이 바뀌면 이전 digest 승인은 실패한다. 이것은 제품 명세 승인이고 기존 생성 도구의 설계 승인·테스트 확정과는 별개다. 게임을 생성하지 않으며 기존 승인 기록을 수정하지 않는다.

관련 58개 검사 통과. 초기 화면·조작 기본값은 사용자와 실제 테스트해 확정한 뒤 명세에 반영한다. 모델 명세 자동 작성과 생성 실행기 연결은 후속 작업이다. 경험 기록 재사용은 2차 자체 제작의 기반이며 모델 자체 학습 완료와 구분한다.
