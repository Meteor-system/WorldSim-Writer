# 草稿驳回/编辑功能实现总结

## ✅ 已完成的功能

### 1. 数据库层
- ✅ 在 `chapter_drafts` 表添加 `rejection_feedback` 字段（Text, 可空）
- ✅ 创建并执行 Alembic 迁移 (版本 0002)

### 2. 后端 API

#### 新增端点
1. **POST `/chapters/{chapter_id}/reject`**
   - 请求体: `{"feedback": "驳回反馈意见"}`
   - 功能: 将章节状态设为 `rejected`，保存用户反馈
   - 返回: 更新后的 DraftResponse

2. **PUT `/chapters/{chapter_id}/draft`**
   - 请求体: `{"content": "新的草稿内容"}`
   - 功能: 更新草稿内容（仅未批准的章节）
   - 返回: 更新后的 DraftResponse

#### 修改的文件
- `backend/app/narrative/models.py` - 添加 `rejection_feedback` 字段
- `backend/app/narrative/schemas.py` - 添加 `RejectRequest` 和 `EditDraftRequest` schema
- `backend/app/narrative/router.py` - 添加两个新端点
- `backend/app/narrative/service.py` - 添加 `reject_chapter()` 和 `edit_chapter_draft()` 函数

### 3. 前端 UI

#### 新增功能
1. **驳回按钮**
   - 点击后弹出输入框，用户输入修改建议
   - 提交后保存反馈并更新草稿状态

2. **编辑按钮**
   - 点击后进入编辑模式
   - 显示可编辑的文本区域
   - 提供"保存修改"和"取消"按钮
   - 保存后更新草稿内容

3. **驳回反馈显示**
   - 如果草稿被驳回，在顶部显示红色提示框
   - 显示用户的驳回反馈意见

#### 修改的文件
- `frontend/src/studio/StudioPage.tsx`
  - 添加 `editMode` 和 `editContent` 状态
  - 添加 `rejectDraft()`, `startEdit()`, `cancelEdit()`, `saveEdit()` 函数
  - 更新 UI 显示驳回反馈和编辑界面

## 🧪 测试方法

### API 测试（使用 curl）

```bash
# 1. 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"***","password":"***"}' \
  | jq -r '.access_token')

# 2. 生成草稿
CHAPTER_ID=$(curl -s -X POST http://localhost:8000/worlds/1/chapters/draft \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chapter_goal":"测试"}' \
  | jq -r '.chapter_id')

# 3. 驳回草稿
curl -X POST http://localhost:8000/chapters/$CHAPTER_ID/reject \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"feedback":"需要更多细节"}'

# 4. 编辑草稿
curl -X PUT http://localhost:8000/chapters/$CHAPTER_ID/draft \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"新的草稿内容..."}'
```

### 前端测试
1. 访问 http://localhost:5173
2. 登录并进入任意世界
3. 进入"创作台"
4. 生成草稿
5. 测试：
   - 点击"驳回"按钮，输入反馈
   - 查看红色驳回反馈框
   - 点击"编辑"按钮，修改内容
   - 点击"保存修改"

## 📊 业务流程

```
生成草稿 → 查看内容
   ↓
[通过] → 更新世界状态
   或
[驳回] → 输入反馈 → 状态变为 rejected
   ↓
[编辑] → 修改内容 → 保存
   ↓
再次审批 → [通过] 或 [再次驳回]
```

## 🔒 权限验证
- 只有章节所属世界的拥有者才能驳回/编辑
- 已批准的章节不能编辑（返回 409 CONFLICT）
- 所有操作都需要有效的 JWT token

## 📝 下一步建议

根据 MVP 需求，还可以添加：
1. **重新生成功能** - 基于驳回反馈重新生成草稿
2. **版本历史** - 记录每次编辑的历史版本
3. **批量操作** - 同时驳回/批准多个章节
4. **评论系统** - 支持多轮反馈讨论

---

**状态**: ✅ 功能完整，API 已注册，前端已更新
**服务**: 后端 (8000) + 前端 (5173) + PostgreSQL (5432) 全部运行中
