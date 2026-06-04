# Studio Candidate Reference Create CTA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Rename the Studio chapter creation CTA when candidate material references are present so users see those references are being used as safe writing context.

**Architecture:** Frontend-only conditional label in `StudioPage`. The button label derives from the active execution context's `material_references` count and does not change the creation payload or approval behavior.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Update the execution-context creation test to click `用候选素材参考创建章节`.
  - Assert generic `创建章节` is not visible while references are present and the chapter is not yet created.
  - Update/preserve the manual/no-reference test to ensure generic `创建章节` remains.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Compute whether the active execution context has material references.
  - Switch only the create button label.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.

---

### Task 1: Studio create CTA names candidate references when present

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing tests**

In `StudioPage.test.tsx`, inside `shows launch execution context summary and submits edited context when creating chapter`, replace:

```ts
await user.click(screen.getByRole('button', { name: '创建章节' }));
```

With:

```ts
expect(screen.queryByRole('button', { name: '创建章节' })).not.toBeInTheDocument();
await user.click(screen.getByRole('button', { name: '用候选素材参考创建章节' }));
```

In `creates manual context when Studio opens without NCC execution context`, before clicking the create button, add:

```ts
expect(screen.getByRole('button', { name: '创建章节' })).toBeInTheDocument();
expect(screen.queryByRole('button', { name: '用候选素材参考创建章节' })).not.toBeInTheDocument();
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "launch execution context summary|manual context"
```

Expected: FAIL because production still renders `创建章节` while candidate references are present.

- [ ] **Step 3: Write minimal implementation**

In `StudioPage.tsx`, after the `executionContext` state is initialized, add:

```ts
const hasMaterialReferences = (executionContext?.material_references ?? []).length > 0;
```

Then replace the create button label:

```tsx
{chapter ? '章节已创建' : '创建章节'}
```

With:

```tsx
{chapter ? '章节已创建' : hasMaterialReferences ? '用候选素材参考创建章节' : '创建章节'}
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "launch execution context summary|manual context"
```

Expected: PASS.

---

### Task 2: Final verification and commit

- [ ] **Step 1: Run backend import safety tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_import_node.py -v
```

Expected: PASS.

- [ ] **Step 2: Run frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Run diff checks**

```bash
git -C /opt/WorldSim-Writer diff --check
```

Expected: no output.

- [ ] **Step 5: Inline self-review and commit**

Review diff for CTA-only scope, unchanged chapter creation payload, unchanged import/canon behavior, unchanged approval behavior, and preserved raw ID/enum hiding, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-studio-candidate-reference-create-cta-design.md docs/superpowers/plans/2026-06-04-studio-candidate-reference-create-cta.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify studio candidate create CTA"
```

Do not push. Do not merge main.
