# Chapter History Localization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. For this session, the user explicitly requires inline execution with no subagents/agents/code-review subagent.

**Goal:** Localize the WorldPage chapter history/review panel and hide raw enum/version tokens from beta-facing copy.

**Architecture:** Keep the existing `ChapterHistoryPanel` component and API types. Import existing display label helpers and add a small value formatter so known status enum values render as Chinese labels while arbitrary author text remains unchanged.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/world/ChapterHistoryPanel.test.tsx`: add failing expectations for localized labels and absence of raw technical tokens.
- Modify `frontend/src/world/ChapterHistoryPanel.tsx`: import label helpers and update visible copy/formatting.
- Create this plan and matching design doc.

---

### Task 1: Add failing chapter-history localization assertions

- [ ] In `frontend/src/world/ChapterHistoryPanel.test.tsx`, update the main render test to expect localized chapter row and detail copy:

```tsx
expect(screen.getByText('已批准章节历史')).toBeInTheDocument();
expect(screen.getByText('第一章 雨巷密谈 · 批准稿第 2 版 · 世界第 1 版 → 第 2 版')).toBeInTheDocument();
expect(await screen.findByText('章节详情')).toBeInTheDocument();
expect(screen.getByText('第一章 雨巷密谈 · 批准稿第 2 版')).toBeInTheDocument();
expect(screen.getByText('世界进度：第 1 版 → 第 2 版')).toBeInTheDocument();
expect(screen.getByText('状态：进行中 → 开始调查密信')).toBeInTheDocument();
expect(screen.getByText('状态：已埋下 → 推进中')).toBeInTheDocument();
expect(screen.getByText('编辑建议：章节冲突清晰，但第二段信息揭示偏快。')).toBeInTheDocument();
expect(screen.getByText('写作依据快照')).toBeInTheDocument();
```

- [ ] Add absence assertions for old English/technical/raw values:

```tsx
expect(document.body).not.toHaveTextContent('Approved Chapter History');
expect(document.body).not.toHaveTextContent('Chapter Detail');
expect(document.body).not.toHaveTextContent('第一章 雨巷密谈 · v2 · 世界 1 → 2');
expect(document.body).not.toHaveTextContent('世界版本：1 → 2');
expect(document.body).not.toHaveTextContent('状态：active → 开始调查密信');
expect(document.body).not.toHaveTextContent('状态：planted → advanced');
expect(document.body).not.toHaveTextContent('Critic：');
expect(document.body).not.toHaveTextContent('执行上下文快照');
```

- [ ] Run RED:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test -- src/world/ChapterHistoryPanel.test.tsx
```

Expected: fail because the panel still renders the old English/raw copy.

---

### Task 2: Localize `ChapterHistoryPanel`

- [ ] In `frontend/src/world/ChapterHistoryPanel.tsx`, import existing helpers:

```tsx
import { labelStatus, labelWorldVersion } from './displayLabels';
```

- [ ] Replace `valueText` with a status-aware formatter:

```tsx
function valueText(value: unknown, fieldName?: string): string {
  if (Array.isArray(value)) return value.map(String).join('、') || '无';
  if (value === null || value === undefined || value === '') return '未设置';
  const text = String(value);
  return fieldName === 'status' ? labelStatus(text) : text;
}
```

- [ ] Update `changeLines` status line:

```tsx
lines.push(`状态：${valueText(change.before?.status, 'status')} → ${valueText(change.after?.status, 'status')}`);
```

- [ ] Replace the list kicker and chapter row title:

```tsx
<p className="chapter-kicker">已批准章节历史</p>
...
{chapter.title} · 批准稿第 {chapter.approved_version} 版 · 世界{labelWorldVersion(chapter.base_world_version)} → {labelWorldVersion(chapter.world_version_after)}
```

- [ ] Replace the detail kicker/version lines:

```tsx
<p className="chapter-kicker">章节复盘</p>
...
{selectedDetail.title} · 批准稿第 {selectedDetail.approved_version} 版
...
世界进度：{labelWorldVersion(selectedDetail.world_version_before)} → {labelWorldVersion(selectedDetail.world_version_after)}
```

- [ ] Replace `Critic` and execution-context labels:

```tsx
<h4 className="font-black text-[#3b2511]">写作依据快照</h4>
...
{selectedDetail.critic_summary && <p className="manuscript rounded-2xl bg-white/35 p-3">编辑建议：{selectedDetail.critic_summary}</p>}
```

- [ ] Run GREEN focused test:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test -- src/world/ChapterHistoryPanel.test.tsx
```

Expected: pass.

---

### Task 3: Verify frontend slice and commit

- [ ] Run related targeted frontend tests:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test -- src/world/ChapterHistoryPanel.test.tsx src/world/WorldPage.test.tsx
```

- [ ] Run frontend build:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run build
```

- [ ] Skip backend pytest and state why: no backend code or API contract changed.

- [ ] Run diff checks:

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add frontend/src/world/ChapterHistoryPanel.tsx frontend/src/world/ChapterHistoryPanel.test.tsx docs/superpowers/specs/2026-06-09-chapter-history-localization-design.md docs/superpowers/plans/2026-06-09-chapter-history-localization.md
git -C /opt/WorldSim-Writer diff --cached --check
```

- [ ] Commit only:

```bash
git -C /opt/WorldSim-Writer commit -m "fix: localize chapter history panel"
```

Do not push or merge.
