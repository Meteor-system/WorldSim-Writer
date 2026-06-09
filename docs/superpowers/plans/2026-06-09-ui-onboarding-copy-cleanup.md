# UI Onboarding Copy Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make key frontend surfaces more author-friendly in Chinese while hiding or friendly-formatting internal enum/id/technical fields.

**Architecture:** Keep this frontend-only. Add display helpers in `frontend/src/world/displayLabels.ts`, then update render-only copy in `WorldArchivePanel.tsx`, `WorldPage.tsx`, and `StudioPage.tsx`; no API/type/schema changes.

**Tech Stack:** Vite React, TypeScript, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/world/displayLabels.ts`
  - Add helpers for snapshot labels, archive file metadata, change types, field names, and source/world-version labels.
- Modify `frontend/src/world/WorldArchivePanel.test.tsx`
  - Test friendlier archive/snapshot/export/compare copy first.
- Modify `frontend/src/world/WorldArchivePanel.tsx`
  - Replace visible internal archive metadata and raw compare labels with friendly copy.
- Modify `frontend/src/world/WorldPage.test.tsx`
  - Test Story Bible and Narrative Control author-friendly headings/help text.
- Modify `frontend/src/world/WorldPage.tsx`
  - Update Story Bible, Story Arc, and Narrative Control copy only.
- Modify `frontend/src/studio/StudioPage.test.tsx`
  - Test Studio context/settlement copy avoids raw internal version/source wording.
- Modify `frontend/src/studio/StudioPage.tsx`
  - Update writing-basis/context and settlement copy.
- Include docs already created:
  - `docs/superpowers/specs/2026-06-09-ui-onboarding-copy-cleanup-design.md`
  - `docs/superpowers/plans/2026-06-09-ui-onboarding-copy-cleanup.md`

---

### Task 1: Archive panel tests and labels

**Files:**
- Modify: `frontend/src/world/WorldArchivePanel.test.tsx`
- Modify: `frontend/src/world/displayLabels.ts`
- Modify: `frontend/src/world/WorldArchivePanel.tsx`

- [ ] **Step 1: Update failing archive tests**

In `WorldArchivePanel.test.tsx`:

- Change the controls test to expect `世界档案库` instead of `World Archive`.
- Change snapshot success expectations from:

```ts
expect(await screen.findByText('快照已创建：版本 3')).toBeInTheDocument();
expect(screen.getByText('Snapshot #12')).toBeInTheDocument();
```

to:

```ts
expect(await screen.findByText('保存点已创建：第 3 版')).toBeInTheDocument();
expect(screen.getByText('可在快照对比中作为回看基准。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('Snapshot #12');
```

- Change export success expectations from raw metadata:

```ts
expect(await screen.findByText('下载包已就绪')).toBeInTheDocument();
expect(screen.getByText('Archive：WorldSim-青岚城-v3-markdown.zip')).toBeInTheDocument();
expect(screen.getByText('格式：zip · 编码：base64 · 内联预览：是')).toBeInTheDocument();
expect(screen.getByText('世界版本：v3 · 文件数：2')).toBeInTheDocument();
```

to:

```ts
expect(await screen.findByText('Obsidian ZIP 已准备好')).toBeInTheDocument();
expect(screen.getByText('下载文件：WorldSim-青岚城-v3-markdown.zip')).toBeInTheDocument();
expect(screen.getByText('世界进度：第 3 版 · Markdown 文件：2 个')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('格式：zip');
expect(document.body).not.toHaveTextContent('编码：base64');
expect(document.body).not.toHaveTextContent('内联预览');
```

- Change compare expectations from:

```ts
expect(screen.getByText('character：1')).toBeInTheDocument();
expect(screen.getByText('字段：status')).toBeInTheDocument();
```

to:

```ts
expect(screen.getByText('角色：1')).toBeInTheDocument();
expect(screen.getByText('变化：资料已更新')).toBeInTheDocument();
expect(screen.getByText('调整项：状态')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('character：1');
expect(document.body).not.toHaveTextContent('字段：status');
```

- [ ] **Step 2: Run archive tests and verify failure**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npx vitest run src/world/WorldArchivePanel.test.tsx
```

Expected: FAIL because UI still shows old/raw copy.

- [ ] **Step 3: Add display helpers**

In `frontend/src/world/displayLabels.ts`, add exports:

```ts
const CHANGE_TYPE_LABELS: Record<string, string> = {
  added: '新增资料',
  removed: '移除资料',
  changed: '资料已更新',
  created: '新增资料',
  updated: '资料已更新',
};

const FIELD_LABELS: Record<string, string> = {
  status: '状态',
  title: '标题',
  name: '名称',
  current_goals: '当前目标',
  public_profile: '公开资料',
  hidden_traits: '隐藏设定',
  description: '描述',
  urgency_level: '紧迫度',
  world_version: '世界进度',
  truth_canon: '正史文本',
  truth_canon_version: '正史修订',
};

export function labelChangeType(value: string): string {
  return CHANGE_TYPE_LABELS[value] ?? readableToken(value);
}

export function labelFieldName(value: string): string {
  return FIELD_LABELS[value] ?? readableToken(value);
}

export function labelSnapshotOption(id: number, version: number, label?: string | null): string {
  return `${label?.trim() || '未命名保存点'} · ${labelWorldVersion(version)}`;
}
```

- [ ] **Step 4: Update `WorldArchivePanel.tsx` copy**

Import `labelChangeType`, `labelFieldName`, `labelObjectType`, `labelSnapshotOption`, `labelWorldVersion`.

Make these render changes:

```tsx
<p className="chapter-kicker">世界档案</p>
<h3 className="mt-2 text-2xl font-black text-[#34210f]">世界档案库</h3>
<p className="manuscript mt-2 text-sm text-[#5e3b1c]">为当前正史创建保存点，或导出可放进 Obsidian 的 Markdown ZIP。</p>
```

Snapshot success block:

```tsx
<p>保存点已创建：{labelWorldVersion(snapshot.world_version)}</p>
<p>可在快照对比中作为回看基准。</p>
<p className="ink-muted">创建时间：{snapshot.created_at}</p>
```

Export success block:

```tsx
<p className="font-black text-[#3b2511]">Obsidian ZIP 已准备好</p>
<p className="manuscript mt-1">导出成功：包含 {markdownExport.files.length} 个 Markdown 文件。</p>
<p className="mt-1 font-bold text-[#5e3b1c]">下载文件：{markdownExport.archive_filename}</p>
<p className="manuscript mt-1 text-sm">世界进度：{labelWorldVersion(markdownExport.world_version)} · Markdown 文件：{markdownExport.files.length} 个</p>
```

Snapshot select options:

```tsx
<option key={item.id} value={item.id}>{labelSnapshotOption(item.id, item.world_version, item.label)}</option>
```

Compare badges and articles:

```tsx
<span key={objectType} ...>{labelObjectType(objectType)}：{count}</span>
<p className="manuscript mt-1 text-sm">{labelObjectType(change.object_type)} · 变化：{labelChangeType(change.change_type)}</p>
{change.fields_changed.length > 0 && <p className="manuscript mt-1 text-sm">调整项：{change.fields_changed.map(labelFieldName).join('、')}</p>}
```

- [ ] **Step 5: Run archive tests and verify pass**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npx vitest run src/world/WorldArchivePanel.test.tsx
```

Expected: PASS.

---

### Task 2: Story Bible and overview copy tests/implementation

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Add/update failing WorldPage tests**

Add a test near existing Story Bible/canon tests, or update existing assertions, to verify:

```ts
await user.click(screen.getByRole('button', { name: '正史资料' }));
expect(screen.getByText('故事圣经')).toBeInTheDocument();
expect(screen.getByText('这里维护后续章节会读取的正式世界设定。适合记录不可轻易改变的世界规则、时间线原则和主角已确认的真相。')).toBeInTheDocument();
expect(screen.getByText('第 2 版 · 设定修订：第 1 次')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('Story Bible');
expect(document.body).not.toHaveTextContent('正史文本版本');
```

Update overview/NCC expectations to expect:

```ts
expect(screen.getByText('故事弧线规划')).toBeInTheDocument();
expect(screen.getByText('下一章准备中心')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('Story Arc Planner');
expect(document.body).not.toHaveTextContent('Narrative Control Center');
```

- [ ] **Step 2: Run WorldPage tests and verify failure**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npx vitest run src/world/WorldPage.test.tsx --pool=forks --maxWorkers=1
```

Expected: FAIL because old copy is still visible.

- [ ] **Step 3: Update `WorldPage.tsx` copy**

Change visible strings:

```tsx
<p className="chapter-kicker">故事圣经</p>
<p className="manuscript mt-2 text-sm text-[#5e3b1c]">这里维护后续章节会读取的正式世界设定。适合记录不可轻易改变的世界规则、时间线原则和主角已确认的真相。</p>
<p className="ink-muted mt-1 text-sm">{labelWorldVersion(world.world_version)} · 设定修订：第 {world.truth_canon_version} 次</p>
```

In edit form under the textarea label, add:

```tsx
<p className="ink-muted mt-1 text-xs">保存后会记录为世界历史，并影响后续草稿读取的正式设定。</p>
```

Change overview section headings:

```tsx
<p className="chapter-kicker">故事弧线规划</p>
<h2 ...>前 10 章故事弧线</h2>
<p className="chapter-kicker">下一章准备中心</p>
<h2 ...>下一章准备中心</h2>
<p ...>查看已写入正史的世界历史记录，并把下一章目标准备好。</p>
```

- [ ] **Step 4: Run WorldPage tests and verify pass**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npx vitest run src/world/WorldPage.test.tsx --pool=forks --maxWorkers=1
```

Expected: PASS.

---

### Task 3: Studio context/settlement copy tests/implementation

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`
- Modify: `frontend/src/world/displayLabels.ts`

- [ ] **Step 1: Update failing Studio tests**

In tests for continuing next chapter and settlement, change expectations:

```ts
expect(screen.getByText('本章写作依据')).toBeInTheDocument();
expect(screen.getByText('依据的世界进度：第 2 版')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('本章执行上下文');
expect(document.body).not.toHaveTextContent('源世界版本：v2');
expect(screen.getByText('世界进度：第 1 版 → 第 2 版')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('世界进度 v1 → v2');
```

Keep API payload assertions for `source_world_version` unchanged because raw API fields are allowed in test payloads, not visible UI.

- [ ] **Step 2: Run Studio tests and verify failure**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npx vitest run src/studio/StudioPage.test.tsx --pool=forks --maxWorkers=1
```

Expected: FAIL because old context/settlement strings are still visible.

- [ ] **Step 3: Update `StudioPage.tsx` copy**

Import `labelWorldVersion` from `../world/displayLabels`.

Change `ExecutionContextSummary`:

```tsx
<h2 className="font-black text-[#3b2511]">本章写作依据</h2>
<p className="mt-3 ink-muted">本章还没有固定写作依据。创建章节时会保存当前目标、世界进度和下一章准备信息。</p>
{frozen && <p className="mt-2 text-sm font-bold text-[#5e3b1c]">写作依据已锁定：{sourceLabel(context.source)} · {labelWorldVersion(context.source_world_version)}</p>}
<p className="mt-2 ink-muted">依据的世界进度：{labelWorldVersion(context.source_world_version)}</p>
```

Change `ExecutionContextSnapshot`:

```tsx
<h3 className="font-black text-[#3b2511]">写作依据快照</h3>
<p className="manuscript text-sm">来源：{sourceLabel(context.source)} · {labelWorldVersion(context.source_world_version)}</p>
```

Change settlement metric:

```tsx
<p className="rounded-2xl bg-white/65 p-3 font-bold text-emerald-950">世界进度：{labelWorldVersion(settlement.worldBefore)} → {labelWorldVersion(settlement.worldAfter)}</p>
```

Change auto-start draft progress line:

```tsx
{draft && <p className="manuscript mt-1 text-sm text-[#26364d]">当前世界进度仍为 {labelWorldVersion(localWorld.world_version)}，草稿依据为 {labelWorldVersion(chapter?.base_world_version ?? localWorld.world_version)}。</p>}
```

- [ ] **Step 4: Run Studio tests and verify pass**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npx vitest run src/studio/StudioPage.test.tsx --pool=forks --maxWorkers=1
```

Expected: PASS.

---

### Task 4: Final frontend verification and commit

**Files:**
- All modified frontend/docs files.

- [ ] **Step 1: Run targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npx vitest run src/world/WorldArchivePanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx --pool=forks --maxWorkers=1
```

Expected: PASS.

- [ ] **Step 2: Run full frontend tests serially**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npx vitest run --pool=forks --maxWorkers=1
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Check diff whitespace**

Run:

```bash
cd /opt/WorldSim-Writer && git diff --check
```

Expected: no output.

- [ ] **Step 5: Inspect status and commit**

Run:

```bash
cd /opt/WorldSim-Writer && git status --short
git add frontend/src/world/displayLabels.ts frontend/src/world/WorldArchivePanel.tsx frontend/src/world/WorldArchivePanel.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx docs/superpowers/specs/2026-06-09-ui-onboarding-copy-cleanup-design.md docs/superpowers/plans/2026-06-09-ui-onboarding-copy-cleanup.md
git diff --cached --check
git commit -m "feat: polish author-facing frontend copy" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Expected: commit succeeds. Do not push or merge.

---

## Self-review

- Spec coverage: archive/export, Story Bible, world overview/Narrative Control, Studio continuous chapter context, tests/build/commit are covered.
- Placeholder scan: no placeholders or vague implementation instructions remain.
- Type consistency: helper names match the plan and existing import style.
