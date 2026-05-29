"""Test full draft generation flow"""
import requests
import json

BASE = 'http://localhost:8000'

# 1. 注册新用户
print('=== 1. 注册用户 ===')
r = requests.post(f'{BASE}/auth/register', json={
    'email': 'writer@test.com',
    'password': 'writer12345',
    'display_name': '小作家'
})
print(f'注册: {r.status_code}')
if r.status_code == 409:
    print('用户已存在，直接登录')

# 2. 登录
print('\n=== 2. 登录 ===')
r = requests.post(f'{BASE}/auth/login', json={
    'email': 'writer@test.com',
    'password': 'writer12345'
})
print(f'登录: {r.status_code}')
if r.status_code != 200:
    print(f'登录失败: {r.text}')
    exit(1)
    
auth_token = r.json().get('access_token', '')
headers = {'Authorization': 'Bearer ' + auth_token}
print('登录成功')

# 3. 获取世界
print('\n=== 3. 获取世界 ===')
r = requests.get(f'{BASE}/worlds', headers=headers)
worlds = r.json()
print(f'世界数量: {len(worlds)}')

if len(worlds) == 0:
    print('创建示例世界...')
    r = requests.post(f'{BASE}/worlds/from-template', headers=headers, json={})
    w = r.json()
    wid = w['id']
    print(f'创建世界: {w["title"]} (ID={wid})')
else:
    wid = worlds[0]['id']
    print(f'使用世界: {worlds[0]["title"]} (ID={wid})')

# 4. 生成草稿
print('\n=== 4. 生成章节草稿 ===')
print('(调用 LLM，可能需要几秒...)')
r = requests.post(f'{BASE}/worlds/{wid}/chapters/draft', headers=headers, json={
    'chapter_goal': '写一个短篇故事开头，主角在雨夜走进一家神秘书店，发现一本会发光的古书'
}, timeout=60)
print(f'生成状态: {r.status_code}')

if r.status_code == 200:
    d = r.json()
    print(f'\n📖 标题: {d["title"]}')
    print(f'📝 内容 ({len(d["content"])} 字):\n')
    print(d['content'])
    print(f'\n📋 上下文摘要: {d["context_summary"]}')
    print(f'🔍 审核提示: {d["review_hints"]}')
else:
    print(f'失败: {r.text}')
