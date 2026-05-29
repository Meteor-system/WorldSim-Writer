import httpx
import json
import os

api_key = os.environ.get("DASHSCOPE_KEY", "")
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

resp = httpx.post(
    base_url + "/chat/completions",
    headers={
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    },
    json={
        "model": "qwen-plus",
        "messages": [{"role": "user", "content": "回复ok两个字"}],
        "max_tokens": 20,
    },
    timeout=15,
)

print("Status: " + str(resp.status_code))
print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
