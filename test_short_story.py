import httpx
import json

base = "http://localhost:8000"

# Login
r = httpx.post(base + "/auth/login", json={"email": "test@worldsim.dev", "password": "test123456"})
token = r.json().get("access_token", r.json().get("token", ""))
headers = {"Authorization": "Bearer " + token}

# Get world
r2 = httpx.get(base + "/worlds", headers=headers)
worlds = r2.json()
world_id = worlds[0]["id"]
world_title = worlds[0].get("title", "")
print(f"世界: {world_title} (ID={world_id})")

# Generate chapter draft - ask for a short ~200 char story
print("\n正在调用 qwen-plus 生成短篇故事...")
r3 = httpx.post(
    f"{base}/worlds/{world_id}/chapters/draft",
    headers=headers,
    json={"chapter_goal": "请生成一个非常简短的短故事章节，大约200字左右。风格轻松有趣，描写主角的一次日常小冒险。"},
    timeout=60,
)

print(f"\n状态码: {r3.status_code}")
if r3.status_code == 200:
    data = r3.json()
    print(f"\n📖 标题: {data.get('title', 'N/A')}")
    content = data.get("draft_content", data.get("content", ""))
    print(f"\n📝 正文 ({len(content)} 字):\n")
    print(content)
    print(f"\n📋 摘要: {data.get('context_summary', 'N/A')}")
    print(f"\n🔍 审核提示:")
    for h in data.get("review_hints", []):
        print(f"  - {h}")
else:
    print(f"错误: {r3.text}")
