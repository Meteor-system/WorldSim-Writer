# Studio Approval Preview Localization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hide raw status enum values in the Studio approval preview checkbox labels.

**Architecture:** Reuse the existing `labelStatus()` helper already imported by `frontend/src/studio/StudioPage.tsx`. Add a tiny local formatter for optional status values and apply it only to approval-preview transition labels; approval selection indexes and API payloads stay unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/studio/StudioPage.test.tsx`: add failing assertions to the existing approval preview test.
- Modify `frontend/src/studio/StudioPage.tsx`: localize approval-preview status transitions.
- Create `docs/superpowers/specs/2026-06-09-studio-approval-preview-localization-design.md`: design note.
- Create `docs/superpowers/plans/2026-06-09-studio-approval-preview-localization.md`: this plan.

---

### Task 1: Add failing Studio approval-preview assertions

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`

- [ ] **Step 1: Add assertions**

In `renders version selector, stash, paragraph controls, diff, and approval preview after drafting`, after the existing `世界进度：1 → 2` / readiness assertions, assert localized approval-preview transitions:

```tsx
expect(screen.getByText('角色：林砚 · 状态：进行中 → 开始调查密信')).toBeInTheDocument();
expect(screen.getByText('伏笔：裂纹玉佩 · 状态：已埋下 → 推进中')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('状态：active → 开始调查密信');
expect(document.body).not.toHaveTextContent('状态：planted → advanced');
```

- [ ] **Step 2: Run RED**

Run:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test -- src/studio/StudioPage.test.tsx
```

Expected: Vitest runs and fails because the approval-preview card still renders raw statuses.

---

### Task 2: Implement localized approval-preview transitions

**Files:**
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Add a local status formatter**

Near the existing helper functions, add:

```tsx
function statusText(value: unknown): string {
  if (value === null || value === undefined || value === '') return '未设置';
  return labelStatus(String(value));
}
```

- [ ] **Step 2: Use the formatter in approval-preview labels**

Change the character checkbox text from:

```tsx
<span>角色：{change.name} · {String(change.before.status ?? '未设置')} → {String(change.after.status ?? '未设置')}</span>
```

to:

```tsx
<span>角色：{change.name} · 状态：{statusText(change.before.status)} → {statusText(change.after.status)}</span>
```

Change the foreshadow checkbox text from:

```tsx
<span>伏笔：{change.title} · {String(change.before.status ?? '未设置')} → {String(change.after.status ?? '未设置')}</span>
```

to:

```tsx
<span>伏笔：{change.title} · 状态：{statusText(change.before.status)} → {statusText(change.after.status)}</span>
```

- [ ] **Step 3: Run GREEN**

Run:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test -- src/studio/StudioPage.test.tsx
```

Expected: targeted Studio test passes.

---

### Task 3: Verify and commit

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run full frontend tests**

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test
```

- [ ] **Step 2: Run frontend build**

```bash
npm --prefix /opt/WorldSim-Writer/frontend run build
```

- [ ] **Step 3: Run diff checks and commit**

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx docs/superpowers/specs/2026-06-09-studio-approval-preview-localization-design.md docs/superpowers/plans/2026-06-09-studio-approval-preview-localization.md
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "fix: localize studio approval preview"
```

Do not push or merge.
