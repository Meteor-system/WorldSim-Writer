# First Chapter Launchpad Candidate Heading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify first-chapter launchpad imported references as candidate writing references.

**Architecture:** Frontend-only copy update in `WorldPage.tsx`. Change the first-chapter launchpad section heading and guardrail sentence only; keep Studio launch handoff, execution context payloads, imported reference rendering, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Update first-chapter launchpad expectations to candidate-material wording.
  - Assert older generic guardrail is not exposed.
  - Preserve raw ID, slug, enum, and canon-safety assertions.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Replace the visible first-chapter launchpad heading and guardrail sentence.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: First-chapter launchpad uses candidate writing reference copy

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Write the failing test**

In the first-chapter launchpad test, replace:

```ts
expect(screen.getAllByText('导入素材参考').length).toBeGreaterThan(0);
expect(screen.getByText('这些素材只会随下一章目标进入创作台，不会自动写入正式设定。')).toBeInTheDocument();
```

With:

```ts
expect(screen.getAllByText('候选素材写作参考').length).toBeGreaterThan(0);
expect(screen.getByText('这些候选素材只会随下一章目标进入创作台，不会自动写入正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('这些素材只会随下一章目标进入创作台，不会自动写入正式设定。');
```

Keep existing raw ID, slug, enum, and canon-safety assertions.

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "shows imported references in the first chapter launchpad"
```

Expected: FAIL because production still renders the older heading and guardrail sentence.

- [ ] **Step 3: Write minimal implementation**

In `WorldPage.tsx`, change:

```tsx
<h3 className="font-black text-[#3b2511]">导入素材参考</h3>
```

To:

```tsx
<h3 className="font-black text-[#3b2511]">候选素材写作参考</h3>
```

And change:

```tsx
<p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">这些素材只会随下一章目标进入创作台，不会自动写入正式设定。</p>
```

To:

```tsx
<p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">这些候选素材只会随下一章目标进入创作台，不会自动写入正式设定。</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "shows imported references in the first chapter launchpad"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for clearer candidate-reference wording, unchanged Studio handoff payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-first-chapter-launchpad-candidate-heading-design.md docs/superpowers/plans/2026-06-04-first-chapter-launchpad-candidate-heading.md frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify first chapter launchpad references"
```

Do not push. Do not merge main.
