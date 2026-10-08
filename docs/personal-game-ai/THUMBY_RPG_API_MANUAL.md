# 일반 Thumby RPG용 입력·저장 API

일반 흑백 Thumby 생성 프로필에서 필요한 입력·저장 API를 선택할 수 있게 했다. 기존 ThumbyDodge용 target.json과 게임 파일은 수정하지 않았다. 이 변경 자체가 RPG 게임 완성이나 실기 검증을 의미하지 않는다.

새 게임 전용 target.json에 다음 항목을 추가한다:

```json
"generation_profile": "thumby",
"thumby_features": ["controls", "save_data"]
```

controls: 십자키 네 방향과 A/B의 pressed/justPressed. L/R은 십자키 좌/우이며 Start 버튼은 없다. save_data: saveData.setName/setItem/getItem/hasItem/save. 저장은 게임명으로 분리하고 명시 시점에 수행한다. CPython 테스트에서는 가짜 기기를 사용한다. 저장 값은 공식 지원 형식으로 인코딩하고 실제 저장·전원 재시작 복구는 실기에서 확인한다.

기능을 생략하면 기존 API 제한을 유지한다. Color, 추측 API, 순수 규칙 모듈의 기기 import를 허용하지 않는다. AST 검사만으로 동적/간접 호출의 모든 동작을 증명하지는 못하므로 생성 테스트와 실기 확인이 필요하다.

검사(ai/personal-game-ai에서): `python -m unittest test_generation_profile test_thumby_capabilities test_production_request`. 관련 전체 98개 검사 통과. 명세→요청 변환은 기존 production_request.py를 사용한다. 제품 명세 승인과 생성 설계·테스트 승인은 별도이며 승인 digest를 임의 변경하지 않는다.

별도 작업 checkout에서 비어 있는 새 게임 폴더와 정확한 expected_branch/edit_directory/branch_document를 준비한다. 생성기에 넘기기 전에 production_request로 명세·설정을 검사한다. 새 게임을 ThumbyDodge 경로에 생성하지 않는다. 경험 자동 재사용·모델 추가 학습은 아직 구현되지 않았다.
