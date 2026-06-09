# Studio Proposed Change Localization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hide raw proposed-change enum values and raw ID fallback strings in the Studio review panel.

**Architecture:** Reuse the existing `labelStatus()` display helper in `frontend/src/studio/StudioPage.tsx`. Change only rendered copy in the proposed changes card; keep API requests, selected indexes, and approval logic unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/studio/StudioPage.test.tsx`: add failing assertions to the existing draft review test.
- Modify `frontend/src/studio/StudioPage.tsx`: localize proposed-change status values and soften missing-name fallbacks.
- Create `docs/superpowers/specs/2026-06-09-studio-proposed-change-localization-design.md`: design note.
- Create `docs/superpowers/plans/2026-06-09-studio-proposed-change-localization.md`: this plan.

---

### Task 1: Add failing Studio test assertions

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`

- [ ] **Step 1: Add assertions**

In `renders version selector, stash, paragraph controls, diff, and approval preview after drafting`, after the approval-preview assertions, add:

```tsx
expect(screen.getByText('拟提交变化只是草稿建议；只有勾选并点击「写入正史并更新世界」后才会更新正式世界。')).toBeInTheDocument();
expect(screen.getByText('开始调查密信')).toBeInTheDocument();
expect(screen.getByText('推进中')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('(advanced)');
expect(document.body).not.toHaveTextContent('角色#');
expect(document.body).not.toHaveTextContent('伏笔#');
```

- [ ] **Step 2: Run RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx
```

Expected: fail because `(advanced)` is still rendered and the explanatory line is missing.

---

### Task 2: Implement localized proposed-change display

**Files:**
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Add explanatory copy**

Inside the `世界状态变化` block, add the explanatory line directly under the heading.

- [ ] **Step 2: Localize status values**

Change:

```tsx
({c.status})
({f.status})
```

to author-facing text using `labelStatus(String(...))`, e.g. `状态：{labelStatus(String(c.status ?? ''))}`.

- [ ] **Step 3: Soften missing-name fallbacks**

Change fallback strings from `角色#${c.character_id}` and `伏笔#${f.foreshadow_id}` to `未命名角色` and `未命名伏笔`.

- [ ] **Step 4: Run GREEN**

Run the targeted Studio test again and expect pass.

---

### Task 3: Verify and commit

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run targeted frontend test**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx
```

- [ ] **Step 2: Run full frontend tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test
```

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

- [ ] **Step 4: Run diff checks and commit**

```bash
cd /opt/WorldSim-Writer
git diff --check
git add frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx docs/superpowers/specs/2026-06-09-studio-proposed-change-localization-design.md docs/superpowers/plans/2026-06-09-studio-proposed-change-localization.md
git diff --cached --check
git commit -m "fix: localize studio proposed changes"
```

Do not push or merge.
