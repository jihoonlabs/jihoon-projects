import json
from urllib.request import urlopen

# 로컬 Ollama 연결 확인: 모델을 실행하지 않는다.
with urlopen("http://127.0.0.1:11434/api/tags", timeout=10) as response:
    data = json.load(response)

for model in data["models"]:
    print("사용 가능한 모델:", model["name"])