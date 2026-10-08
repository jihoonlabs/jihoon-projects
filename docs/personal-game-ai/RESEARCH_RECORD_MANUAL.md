# 조사 근거 연결 — MANUAL

장르·기기 기획에 조사 근거를 연결하는 CLI를 추가했다. 기기 정보 혼용과 미확인 자료의 확정 취급을 막는다. 기존 제작 실행기는 변경하지 않았다.

evidence.json 예시 (미확인 항목 예제이며 실측 결과가 아님):

```json
{
  "device": "thumby",
  "entries": [
    {
      "category": "hardware",
      "topic": "화면 가독성",
      "finding": "사용자 화면 테스트 필요",
      "source": "",
      "checked_on": "2026-10-08",
      "status": "unknown"
    }
  ]
}
```

저장소 루트에서:

```sh
python ai/personal-game-ai/research_record.py --brief game-brief.json --evidence evidence.json --output researched-brief.json
```

documented는 자료 URL, measured는 실제 측정 기록 참조를 적는다. 이 CLI는 출처 내용을 확인하거나 웹을 조사하지 않는다. 새 출력 파일에 기록하고 원본·기존 출력을 덮어쓰지 않는다. 입력이 완성된 기획만 사용하며 조사 기록이 생겨도 게임 제작 승인은 미확정이다.

검사:

```sh
cd ai/personal-game-ai
python -m unittest test_game_brief test_research_record test_request_intake test_workflow_bridge
```

46개 검사 통과. 조사 입력 연결까지 구현했고 자동 조사·축소 선택지·명세 승인·Color 게임 생성은 아직 미구현이다. 초기 화면과 조작감은 함께 테스트하고 확정 기본값 위의 반복 제작을 맡기는 방향을 다음 단계에 유지한다.
