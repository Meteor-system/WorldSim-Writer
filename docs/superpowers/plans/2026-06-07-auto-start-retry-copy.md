# Auto-Start Retry Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this run. Do not use subagents, agents, code-review subagents, or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the auto-start first-draft failure message with the explicit retry CTA so users know exactly how to continue after a created world is preserved.

**Architecture:** Keep this frontend-only in `StudioPage`. Change only the failure-detail copy shown when `launchContext.autoStartFirstDraft` is active, an error exists, and no draft exists. Preserve retry behavior, chapter creation behavior, canon boundary, world version, EventLog, and approval behavior.

**Tech Stack:** React, TypeScript, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/studio/StudioPage.test.tsx` — update the auto-start failure regression to require the new CTA-specific recovery copy and reject the stale lower-button instruction.
- Modify `frontend/src/studio/StudioPage.tsx` — update the failure-detail copy in `autoStartNoticeDetail`.

---

### Task 1: Add RED coverage for CTA-specific retry copy

- [ ] **Step 1: Update the auto-start failure test**

In `frontend/src/studio/StudioPage.test.tsx`, inside `shows a friendly retry path when auto-start first draft fails`, replace the stale detail assertion:

```ts
expect(screen.getByText('世界已经保留；请检查章节目标后点击下方创建章节按钮手动重试。')).toBeInTheDocument();
```

with:

```ts
expect(screen.getByText('世界已经保留；请检查章节目标后点击“重新创建第一章草稿”重试。')).toBeInTheDocument();
expect(screen.queryByText('世界已经保留；请检查章节目标后点击下方创建章节按钮手动重试。')).not.toBeInTheDocument();
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: fails because the production copy still references the lower create button.

---

### Task 2: Update the failure detail copy

- [ ] **Step 1: Change the failure-detail string**

In `frontend/src/studio/StudioPage.tsx`, change the `autoStartNoticeDetail` failure branch from:

```tsx
? '世界已经保留；请检查章节目标后点击下方创建章节按钮手动重试。'
```

to:

```tsx
? '世界已经保留；请检查章节目标后点击“重新创建第一章草稿”重试。'
```

- [ ] **Step 2: Verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: all StudioPage tests pass.

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
git -C /opt/WorldSim-Writer add docs/superpowers/plans/2026-06-07-auto-start-retry-copy.md frontend/src/studio/StudioPage.test.tsx frontend/src/studio/StudioPage.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "fix: align first draft retry copy"
```

Expected: commit succeeds on current branch. Do not push. Do not merge.

---

## Inline Self-Review

- Spec coverage: tightens the Next-3 retry path by making recovery copy match the explicit retry CTA.
- Scope check: frontend-only copy/test change; no API, canon, EventLog, auto-start, world version, or approval behavior changes.
- TDD check: test fails first on stale copy, then minimal string change passes.
- Placeholder scan: no TBD/TODO placeholders.
