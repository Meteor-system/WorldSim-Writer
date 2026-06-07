# Brief Create First-Draft Submit Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this run. Do not use subagents, agents, code-review subagents, or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the one-sentence open-book form clearly state that confirming a brief-generated draft will create the world and enter first-chapter draft review, without writing 正史.

**Architecture:** Keep this frontend-only in `WorldCreationForm`. Use the existing `briefDraftApplied` state to switch the confirmation copy and submit button label after a one-sentence draft is applied. Do not change API payloads, world creation behavior, Studio auto-start behavior, world versions, or EventLog behavior.

**Tech Stack:** React, TypeScript, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/world/WorldCreationForm.test.tsx` — add RED assertions for brief-applied submit copy and manual-form absence.
- Modify `frontend/src/world/WorldCreationForm.tsx` — render phase-specific confirmation copy and button label when `briefDraftApplied` is true.

---

### Task 1: Add RED tests for brief-created first-draft confirmation copy

- [ ] **Step 1: Strengthen one-sentence draft fill test**

In `frontend/src/world/WorldCreationForm.test.tsx`, update `fills the editable form from a one-sentence draft without creating a world` after the existing "现在还没有创建世界" assertion with:

```ts
expect(screen.getByText('确认创建后会进入第一章草稿审阅；第一章仍需在创作台点击“写入正史并更新世界”才会正式生效。')).toBeInTheDocument();
expect(screen.getByRole('button', { name: '创建世界并生成第一章草稿' })).toBeInTheDocument();
expect(screen.queryByRole('button', { name: '创建自定义世界' })).not.toBeInTheDocument();
```

- [ ] **Step 2: Add manual-form absence assertion**

In `submits a custom world payload with starter assets`, before clicking the submit button, add:

```ts
expect(screen.getByRole('button', { name: '创建自定义世界' })).toBeInTheDocument();
expect(screen.queryByRole('button', { name: '创建世界并生成第一章草稿' })).not.toBeInTheDocument();
expect(screen.queryByText('确认创建后会进入第一章草稿审阅；第一章仍需在创作台点击“写入正史并更新世界”才会正式生效。')).not.toBeInTheDocument();
```

- [ ] **Step 3: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx --run
```

Expected: fails because the first-draft confirmation copy and submit label are not implemented yet.

---

### Task 2: Implement brief-applied confirmation copy

- [ ] **Step 1: Add confirmation text in the brief success panel**

In `frontend/src/world/WorldCreationForm.tsx`, inside the `briefSuccess` section, after the existing line:

```tsx
<p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">现在还没有创建世界，也没有写入正史。只有点击“创建自定义世界”后才会创建。</p>
```

replace it with phase-aware copy:

```tsx
<p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">现在还没有创建世界，也没有写入正史。只有点击“创建世界并生成第一章草稿”后才会创建。</p>
<p className="manuscript mt-1 text-sm font-bold text-[#5e3b1c]">确认创建后会进入第一章草稿审阅；第一章仍需在创作台点击“写入正史并更新世界”才会正式生效。</p>
```

This copy only appears inside the `briefSuccess` block, so manual and seed flows do not show it.

- [ ] **Step 2: Switch the submit button label for brief-applied drafts**

In the final submit button, replace:

```tsx
{creating ? '正在冻结初始真理库...' : '创建自定义世界'}
```

with:

```tsx
{creating ? '正在冻结初始真理库...' : briefDraftApplied ? '创建世界并生成第一章草稿' : '创建自定义世界'}
```

- [ ] **Step 3: Verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx --run
```

Expected: all `WorldCreationForm` tests pass.

---

### Task 3: Final verification and commit

- [ ] **Step 1: Run related Next-3 regression tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx --run
```

Expected: all targeted tests pass.

- [ ] **Step 2: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 3: Run diff checks and commit**

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add docs/superpowers/plans/2026-06-07-brief-create-first-draft-submit-copy.md frontend/src/world/WorldCreationForm.test.tsx frontend/src/world/WorldCreationForm.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "fix: clarify brief-created first draft path"
```

Expected: commit succeeds on current branch. Do not push. Do not merge.

---

## Inline Self-Review

- Spec coverage: closes a Next-3 clarity gap before users submit a brief-generated world, making the create -> first draft review path explicit.
- Scope check: frontend-only copy and label change; no API, canon, EventLog, or auto-start logic changes.
- Placeholder scan: no TBD/TODO placeholders.
