import re
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

# 외부 API 대신 맥 안의 Ollama에 요청한다.
payload = {
    "model": "qwen3-coder:30b",
    "messages": [
        {
            "role": "system",
            "content": (
                "너는 TinyCircuits Thumby(썸비) 게임 개발 도우미다. "
                "일반 썸비는 thumby 모듈을 사용하는 MicroPython 기기다. "
                "썸비와 썸비 컬러의 API를 혼동하지 마라. "
                "모르는 API는 추측하지 말고 공식 자료 확인이 필요하다고 말해라. "
                "한국어로 간결하게 답하고, 요청한 항목 수를 지켜라. "
                "실제로 수행하지 않은 파일 수정이나 검사를 했다고 말하지 마라."
            ),
        },
        {
            "role": "user",
            "content": "",
        },
    ],
    "stream": False,
    "options": {
        "num_ctx": 8192,
        "num_predict": 1024,
        "temperature": 0,
    },
    # 응답이 끝나면 모델 메모리를 해제한다.
    "keep_alive": 0,
}

class ModelLengthError(RuntimeError):
    """Keep the incomplete response available to the caller for diagnostics."""

    def __init__(self, result):
        super().__init__("AI 응답이 길이 제한으로 중단됐습니다.")
        self.result = result


def model_options():
    options = payload["options"].copy()
    for name, minimum, maximum in (
        ("num_ctx", 1024, 131072), ("num_predict", 1, 32768)
    ):
        value = os.environ.get("GAME_AI_" + name.upper())
        if value is not None:
            try:
                number = int(value)
            except ValueError:
                raise ValueError(f"GAME_AI_{name.upper()}는 정수여야 합니다.") from None
            if not minimum <= number <= maximum:
                raise ValueError(f"GAME_AI_{name.upper()} 범위: {minimum}..{maximum}")
            options[name] = number
    if options["num_predict"] >= options["num_ctx"]:
        raise ValueError("num_predict는 num_ctx보다 작아야 합니다.")
    return options


def ask_model(prompt):
    # 호출할 때마다 독립된 요청 데이터를 만든다.
    data = {
        **payload,
        "options": model_options(),
        "messages": [
            payload["messages"][0].copy(),
            {"role": "user", "content": prompt},
        ],
    }

    api_request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(api_request, timeout=600) as response:
        result = json.load(response)

    # 응답 한도에 도달하면 완성된 결과로 취급하지 않는다.
    if result.get("done_reason") == "length":
        raise ModelLengthError(result)

    return result["message"]["content"]

if __name__ == "__main__":
    prompt = input("AI에게 맡길 요청: ")
    payload["messages"][-1]["content"] = prompt

    print("AI 응답을 기다리는 중...", flush=True)
    answer = ask_model(prompt)
    print(answer)

    # 이 프로그램 옆의 outputs 폴더에 요청과 응답을 저장한다.
    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".md"
    output_path = output_dir / filename

    content = (
        "# 요청\n\n"
        + payload["messages"][-1]["content"]
        + "\n\n# 응답\n\n"
        + answer
        + "\n"
    )
    output_path.write_text(content, encoding="utf-8")
    print("저장 위치:", output_path)

    # Python 코드 블록이 하나일 때만 별도 파일로 저장한다.
    code_blocks = re.findall(r"```python\s*\n(.*?)```", answer, re.DOTALL)

    if len(code_blocks) == 1:
        code_path = output_path.with_suffix(".py")
        code = code_blocks[0].strip() + "\n"
        code_path.write_text(code, encoding="utf-8")
        print("코드 저장 위치:", code_path)

        # 코드를 실행하지 않고 문법만 검사한다.
        try:
            compile(code, str(code_path), "exec")
        except SyntaxError as error:
            print("문법 검사 실패:", error)
        else:
            print("문법 검사 통과")
