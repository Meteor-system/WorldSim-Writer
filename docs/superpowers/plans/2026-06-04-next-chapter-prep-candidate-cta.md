# Next Chapter Prep Candidate CTA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Rename the next-chapter Studio launch CTA when candidate material references are present so users see those references will enter Studio safely.

**Architecture:** Frontend-only conditional copy in `NextChapterPrepPanel`. Tests cover both material-reference and no-reference CTA labels while preserving the existing execution context payload.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
  - In the existing material-reference test, click `带下一章候选素材参考进入创作台` and assert the generic CTA is absent.
  - Add a no-reference test that keeps `进入创作台并使用此目标`.
  - Preserve raw ID/enum/slug hiding and callback payload assertions.
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`
  - Compute whether candidate references exist and switch the primary CTA label only.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.

---

### Task 1: Next-chapter CTA names candidate references when present

**Files:**
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`

- [ ] **Step 1: Write the failing tests**

In `NextChapterPrepPanel.test.tsx`, inside `renders next chapter prep signals and uses suggested goal callback`, replace:

```ts
await user.click(screen.getByRole('button', { name: '进入创作台并使用此目标' }));
```

With:

```ts
expect(screen.queryByRole('button', { name: '进入创作台并使用此目标' })).not.toBeInTheDocument();
await user.click(screen.getByRole('button', { name: '带下一章候选素材参考进入创作台' }));
```

Then add this test before `renders loading and error states`:

```ts
  it('keeps the generic studio CTA when no candidate references exist', () => {
    render(<NextChapterPrepPanel prep={{ ...prep, material_references: [] }} onEnterStudioWithContext={vi.fn()} />);

    expect(screen.getByRole('button', { name: '进入创作台并使用此目标' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '带下一章候选素材参考进入创作台' })).not.toBeInTheDocument();
    expect(screen.queryByText('候选素材写作参考')).not.toBeInTheDocument();
  });
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx -t "suggested goal callback|generic studio CTA"
```

Expected: FAIL because production still renders `进入创作台并使用此目标` even when candidate references exist.

- [ ] **Step 3: Write minimal implementation**

In `NextChapterPrepPanel.tsx`, after:

```ts
const context = buildExecutionContextFromPrep(prep);
```

Add:

```ts
const hasMaterialReferences = (prep.material_references ?? []).length > 0;
```

Then replace:

```tsx
进入创作台并使用此目标
```

With:

```tsx
{hasMaterialReferences ? '带下一章候选素材参考进入创作台' : '进入创作台并使用此目标'}
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx -t "suggested goal callback|generic studio CTA"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/studio/StudioPage.test.tsx
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

Review diff for CTA-copy scope, unchanged context payload behavior, unchanged import/canon behavior, and preserved raw ID/enum hiding, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-next-chapter-prep-candidate-cta-design.md docs/superpowers/plans/2026-06-04-next-chapter-prep-candidate-cta.md frontend/src/world/NextChapterPrepPanel.tsx frontend/src/world/NextChapterPrepPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify next chapter candidate CTA"
```

Do not push. Do not merge main.
