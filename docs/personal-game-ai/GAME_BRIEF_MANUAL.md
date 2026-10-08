# 장르·기기 입력 — MANUAL

원하는 장르·핵심 재미와 타겟 기기를 먼저 기록하는 실제 CLI를 추가했다. 기존 입력기는 일반 Thumby 생성용이므로 Color를 잘못된 실행기에 넘기지 않도록 조사 전 기획 파일을 별도로 만든다.

저장소 루트에서 실행:

```sh
python ai/personal-game-ai/game_brief.py --device thumby --interactive --output game-brief.json
```

장르와 핵심 재미 두 질문에 답하면 파일이 생긴다. Color 기획은 --device thumby-color로 지정한다. 기존 파일 이름이면 저장을 거부하므로 다른 이름을 사용한다. 기획 입력 파일만 저장하며 게임 생성이나 승인은 실행하지 않는다.

검사:

```sh
cd ai/personal-game-ai
python -m unittest test_game_brief test_request_intake test_workflow_bridge
```

39개 검사 통과. 기존 입력·워크플로 연결 코드는 변경하지 않았다. Ollama·Docker 없이 실행 가능하지만, 조사 자동화·축소 선택지·명세 승인·Color 생성은 아직 구현하지 않았다. 이번 작업은 도구의 첫 입력 단계 구현이며 전체 제작 도구 완료를 의미하지 않는다.
