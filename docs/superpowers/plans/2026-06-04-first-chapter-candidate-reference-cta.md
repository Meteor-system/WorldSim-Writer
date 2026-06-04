# First Chapter Candidate Reference CTA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Make the first-chapter launchpad CTA explicit when candidate material references will be carried into Studio.

**Architecture:** Frontend-only conditional copy in `FirstChapterLaunchpad`. The component already receives `materialReferences` and calls `onLaunchChapter(nextChapter)`, so this change updates only the button label while preserving existing data flow into Studio execution context.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Update the existing first-chapter launchpad candidate-reference test to look for the candidate-aware CTA.
  - Preserve assertions that material references are carried into Studio and raw IDs/enums/slugs are hidden.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Make the first-chapter launchpad primary CTA conditional on `materialReferences.length > 0`.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.

---

### Task 1: Candidate references make the launchpad CTA explicit

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Write the failing test**

In `WorldPage.test.tsx`, inside `shows imported references in the first chapter launchpad and carries them into Studio context`, replace:

```ts
await user.click(screen.getByRole('button', { name: '用此目标进入创作台' }));
```

With:

```ts
expect(screen.getByRole('button', { name: '带候选素材参考进入创作台' })).toBeInTheDocument();
expect(screen.queryByRole('button', { name: '用此目标进入创作台' })).not.toBeInTheDocument();

await user.click(screen.getByRole('button', { name: '带候选素材参考进入创作台' }));
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "first chapter launchpad"
```

Expected: FAIL because production still renders the generic `用此目标进入创作台` button when candidate references exist.

- [ ] **Step 3: Write minimal implementation**

In `WorldPage.tsx`, replace:

```tsx
<button className="primary-button" type="button" onClick={() => onLaunchChapter(nextChapter)}>用此目标进入创作台</button>
```

With:

```tsx
<button className="primary-button" type="button" onClick={() => onLaunchChapter(nextChapter)}>
  {materialReferences.length > 0 ? '带候选素材参考进入创作台' : '用此目标进入创作台'}
</button>
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "first chapter launchpad"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for candidate-aware CTA wording, unchanged Studio payload behavior, unchanged import/canon behavior, and preserved raw ID/enum hiding, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-first-chapter-candidate-reference-cta-design.md docs/superpowers/plans/2026-06-04-first-chapter-candidate-reference-cta.md frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify candidate launchpad CTA"
```

Do not push. Do not merge main.
