# 축소안 선택 — MANUAL

조사 기획에 축소 선택지를 연결하고 사용자가 고른 안을 저장한다. 선택 자체가 게임 제작이나 최종 명세 승인으로 처리되지 않는다.

proposal.json 예시 (성능이 검증된 추천이 아닌 입력 예제):

```json
{
  "device": "thumby",
  "options": [
    {"id": "small", "title": "한 화면", "keep": ["거리 싸움"], "reduce": ["적 한 명"], "unverified": ["실기 속도"]},
    {"id": "stage", "title": "짧은 스테이지", "keep": ["이동과 전투"], "reduce": ["스테이지 한 개"], "unverified": ["메모리와 가독성"]}
  ]
}
```

저장소 루트:

```sh
python ai/personal-game-ai/downscale_choice.py --brief researched-brief.json --proposal proposal.json --interactive --output chosen-brief.json
```

유지·축소·미검증 항목을 읽고 ID를 입력한다. 비대화 모드는 --interactive 대신 --select small을 사용한다. 선택 없이 제안 파일만 저장하려면 두 옵션을 생략한다. 게임 형식과 기기 조사 자료가 모두 필요하며 모르는 항목은 unknown으로 기록한다. 기존 출력 파일은 덮어쓰지 않는다.

관련 입력·조사·선택·기존 연결 검사 52개 통과. 실제 모델의 축소안 생성, 내용 검토, 명세 승인과 게임 제작 연결은 아직 미구현이다. 사용자의 초기 화면 테스트로 기본값을 잡고 이후 반복 제작을 맡기는 방향을 유지한다. 1차는 제작 도구이며 2차의 경험 활용·실제 학습은 별도 후속 단계다.
