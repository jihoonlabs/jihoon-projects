# 요청에서 생성 도구로 연결

이번 기능은 요청 질문과 저장 후 기존 생성 도구를 바로 호출합니다. JSON을 복사하거나 workflow용 요청 파일을 다시 작성할 필요가 없습니다. 별도 생성 작업 폴더를 명시하며 기존 브랜치·문맥 검사를 우회하지 않습니다.

```bash
cd ai/personal-game-ai
python request_intake.py --interactive --workflow-dir /실제/생성checkout/ai/personal-game-ai
```

위 경로는 예시입니다. 집의 실제 생성 작업 폴더로 바꾸세요. 새 게임의 대상 폴더·허용 API·브랜치 문서를 먼저 준비한 후 실행해야 합니다. 현재 Child 자체는 기존 target.json과 브랜치가 다르므로 생성 폴더로 지정하면 차단됩니다. --infer를 추가하면 설정 추출에도 Ollama를 사용합니다.

결과에는 stage와 request_file이 표시됩니다. review_design이면 설계 내용을 확인해야 하며 자동 승인하지 않습니다. 확인한 digest를 그대로 전달하면 같은 요청으로 다음 단계에 연결됩니다.

```bash
python workflow_bridge.py --request /출력된/요청파일.json --tool-dir /실제/생성도구폴더 --approve-design 확인한설계digest
python workflow_bridge.py --request /같은/요청파일.json --tool-dir /같은/생성도구폴더 --confirm-tests 확인한테스트digest
```

승인 없이 조회·재개하려면 마지막 승인 옵션을 빼세요. 대상 문맥이 달라지면 기존 engine이 새 실행 기록을 만들 수 있으므로 같은 문맥에서 재개해야 합니다. 기존 집 workflow가 완료돼 있다면 먼저 결과 검토를 하세요. 이 새 요청으로 기존 기록을 덮어쓰거나 승인 digest를 수정하지 않습니다.

모델이 구현 중 설정 질문에서 멈췄다면 --interactive로 같은 요청을 재개하세요. 터미널에 질문이 표시되고 답하면 최신 상태로 이어집니다. 최초 request_intake의 --workflow-dir 연결에서도 이 대화 모드가 적용됩니다. /stop 또는 입력 종료로 멈출 수 있으며 현재 단계와 요청 파일은 유지됩니다. 빈 답변·4000자 초과는 제출하지 않고 멈춥니다. 한 실행의 질문은 최대 20회이며 한도에 도달하면 같은 명령으로 다시 재개할 수 있습니다.

```bash
python workflow_bridge.py --request /같은/요청파일.json --tool-dir /같은/생성도구폴더 --interactive
```

설계 검토·테스트 검토·Git 커밋 대기·오류·완료에서는 대화를 끝내고 결과를 표시합니다. 승인하지 않은 설계나 테스트를 자동 통과시키지 않습니다. 설계·테스트 생성이 중단된 경우에만 --retry로 명시 재시도할 수 있습니다. 실제 허용 상태와 잠금은 기존 engine이 검사하며 자동 재시도는 하지 않습니다. 질문 ID를 직접 지정하는 방식도 유지합니다.

```bash
python workflow_bridge.py --request /같은/요청파일.json --tool-dir /같은/생성도구폴더 --answer 002 --answer-text '확인한 게임 설정'
python workflow_bridge.py --request /같은/요청파일.json --tool-dir /같은/생성도구폴더 --retry
```

답변 ID/내용은 함께 지정해야 하고 승인·확정·답변·재시도는 한 번에 하나만 사용합니다. 답변은 1~4000자이며 연결기는 원문을 셸 명령으로 해석하지 않습니다. 잠금 파일을 임의로 지우거나 digest를 수정하지 마세요.

연결/입력 검사 30개와 전체 323개 테스트가 통과했습니다. 실제 생성 engine의 브랜치 불일치 차단과 가짜 engine을 사용한 CLI 대화·검토 정지도 확인했습니다. 실제 Ollama·Docker를 통한 성공 실행, 새 게임 생성, 기기 전달은 아직 미검증입니다. 테스트 피드백·설계 수정 연결은 남아 있습니다.

폰에서는 이전 검사 파일 PASS 5를 확인했습니다. 긴 로그 복사 없이 짧은 결과 확인이 가능하지만 이번 생성 연결의 성공까지 검증한 것은 아닙니다. 이번 변경은 Child commit·push로 남기며 merge하지 않습니다.
