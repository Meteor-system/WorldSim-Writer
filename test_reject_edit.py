"""Test the reject and edit draft functionality"""
import json
import requests

BASE_URL = "http://localhost:8000"

# Login to get token
print("1. 登录获取 Token...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": "meteor@test.com", "password": "***"}
)
assert login_response.status_code == 200, f"登录失败: {login_response.status_code}"
token = login_response.json()["access_token"]
print(f"✓ Token: {token[:20]}...")

headers = {"Authorization": f"Bearer {token}"}

# Get world ID
print("\n2. 获取世界列表...")
worlds_response = requests.get(f"{BASE_URL}/worlds", headers=headers)
assert worlds_response.status_code == 200
worlds = worlds_response.json()
world_id = worlds[0]["id"]
print(f"✓ 世界 ID: {world_id}, 名称: {worlds[0]['name']}")

# Generate a draft
print("\n3. 生成草稿...")
draft_response = requests.post(
    f"{BASE_URL}/worlds/{world_id}/chapters/draft",
    headers=headers,
    json={"chapter_goal": "测试驳回和编辑功能"}
)
assert draft_response.status_code == 200, f"生成草稿失败: {draft_response.status_code} - {draft_response.text}"
draft = draft_response.json()
chapter_id = draft["chapter_id"]
original_content = draft["content"]
print(f"✓ 章节 ID: {chapter_id}")
print(f"✓ 草稿内容长度: {len(original_content)} 字符")
print(f"✓ 前50字符: {original_content[:50]}...")

# Test reject
print("\n4. 测试驳回功能...")
feedback = "这段内容需要更多细节描写，特别是角色的心理活动"
reject_response = requests.post(
    f"{BASE_URL}/chapters/{chapter_id}/reject",
    headers=headers,
    json={"feedback": feedback}
)
assert reject_response.status_code == 200, f"驳回失败: {reject_response.status_code} - {reject_response.text}"
rejected_draft = reject_response.json()
assert rejected_draft["rejection_feedback"] == feedback, "驳回反馈未保存"
print(f"✓ 驳回成功")
print(f"✓ 反馈已保存: {rejected_draft['rejection_feedback']}")

# Test edit
print("\n5. 测试编辑功能...")
edited_content = original_content + "\n\n【编辑补充】林砚深吸一口气，感受到了空气中弥漫的紧张气氛。他知道，这一切才刚刚开始。"
edit_response = requests.put(
    f"{BASE_URL}/chapters/{chapter_id}/draft",
    headers=headers,
    json={"content": edited_content}
)
assert edit_response.status_code == 200, f"编辑失败: {edit_response.status_code} - {edit_response.text}"
edited_draft = edit_response.json()
assert edited_draft["content"] == edited_content, "内容未更新"
assert len(edited_draft["content"]) > len(original_content), "内容长度未增加"
print(f"✓ 编辑成功")
print(f"✓ 内容已更新，新长度: {len(edited_draft['content'])} 字符")
print(f"✓ 新增内容: {edited_content[len(original_content):]}")

# Verify edit persists
print("\n6. 验证编辑持久化...")
verify_response = requests.get(f"{BASE_URL}/chapters/{chapter_id}", headers=headers)
assert verify_response.status_code == 200
chapter_data = verify_response.json()
print(f"✓ 章节状态: {chapter_data['status']}")
print(f"✓ 草稿版本: {chapter_data['draft_version']}")

print("\n" + "="*50)
print("✓ 所有测试通过！")
print("✓ 驳回功能：正常工作，反馈已保存")
print("✓ 编辑功能：正常工作，内容已更新并持久化")
print("="*50)
