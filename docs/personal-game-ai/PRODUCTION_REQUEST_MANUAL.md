# 승인 명세의 생성 요청 변환

승인한 제작 명세를 기존 생성기가 읽는 요청 형식으로 변환한다. 승인 내용이 바뀌거나 대상 브랜치·게임 폴더가 다르면 중단한다. 게임 코드 생성 기능은 아니다.

먼저 별도 작업 checkout에서 새 게임용 빈 폴더와 대상 설정을 준비한다. ThumbyDodge의 target.json을 다른 게임에 그대로 사용하지 않는다. 대상 설정의 expected_branch·edit_directory는 명령의 값과 일치해야 한다.

```sh
python ai/personal-game-ai/production_request.py \
  --record /absolute/path/approved_specification.json \
  --target-config /absolute/path/new-engine/ai/personal-game-ai/target.json \
  --game-directory micropython/NewGame \
  --expected-branch work/new-game \
  --output-dir /absolute/path/new-request-bundle
```

출력의 request.json이 생성기 입력이고 binding.json은 승인 digest·대상 설정·문맥·제한 사항을 확인할 기록이다. 출력 폴더는 새 경로를 사용한다. 문서의 명령은 형식 예시이며 아직 생성 환경을 자동 준비하지 않는다.

명세를 줄여서 통과시키지 않는다. 생성기 길이 제한에 맞지 않으면 차단하며 이 경우 요청 전달 구조를 개선하거나 명세를 다시 검토해야 한다. 기존 workflow는 binding.json을 자동 검사하지 않는다. 다른 checkout으로 전달하기 전 대상 설정을 다시 확인해야 한다.

검사: `python -m unittest test_production_request test_production_spec test_workflow_bridge` (ai/personal-game-ai에서 실행). 관련 총 49개 검사 통과. 실제 모델·게임 플레이는 미검증이다. RPG의 A/B·위/아래·저장 API 생성 지원은 별도 확장이 필요하다. 게임 완성·경험 자동 재사용·모델 학습 완료를 의미하지 않는다.
