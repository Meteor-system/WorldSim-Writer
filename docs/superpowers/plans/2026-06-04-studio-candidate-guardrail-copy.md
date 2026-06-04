# Studio Candidate Guardrail Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify Studio imported-reference guardrails as candidate-material writing references.

**Architecture:** Frontend-only copy update in `StudioPage.tsx`. Change three visible Studio guardrail strings only; keep execution context payloads, draft generation, approval behavior, settlement data, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Update Studio execution context, frozen snapshot, and settlement expectations to candidate-material wording.
  - Assert older generic guardrails are not exposed.
  - Preserve raw ID, slug, enum, and canon-safety assertions.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Replace the visible Studio imported-reference guardrail strings.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Studio uses candidate-material guardrails

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing tests**

In `StudioPage.test.tsx`, replace the execution-context guardrail expectation:

```ts
expect(screen.getByText('导入素材只是本章写作参考，不会自动改写正式设定。')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('候选素材只是本章写作参考，不会自动改写正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('导入素材只是本章写作参考，不会自动改写正式设定。');
```

Replace the frozen snapshot expectation:

```ts
expect(screen.getByText('素材参考不会自动改写正式设定。')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('候选素材参考不会自动改写正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('素材参考不会自动改写正式设定。');
```

Replace the settlement expectation:

```ts
expect(screen.getByText('导入素材仍是本章创作参考，没有自动写入正式设定。')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('候选素材仍是本章创作参考，没有自动写入正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('导入素材仍是本章创作参考，没有自动写入正式设定。');
```

Keep existing raw ID, slug, enum, and canon-safety assertions.

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "launch execution context summary|frozen execution context snapshot|world progression settlement"
```

Expected: FAIL because production still renders the older Studio guardrail strings.

- [ ] **Step 3: Write minimal implementation**

In `StudioPage.tsx`, change:

```tsx
{compact ? '素材参考不会自动改写正式设定。' : '导入素材只是本章写作参考，不会自动改写正式设定。'}
```

To:

```tsx
{compact ? '候选素材参考不会自动改写正式设定。' : '候选素材只是本章写作参考，不会自动改写正式设定。'}
```

And change:

```tsx
<p className="manuscript mt-2 text-sm">导入素材仍是本章创作参考，没有自动写入正式设定。</p>
```

To:

```tsx
<p className="manuscript mt-2 text-sm">候选素材仍是本章创作参考，没有自动写入正式设定。</p>
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "launch execution context summary|frozen execution context snapshot|world progression settlement"
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

Review diff for clearer Studio candidate-reference wording, unchanged execution context and approval payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-studio-candidate-guardrail-copy-design.md docs/superpowers/plans/2026-06-04-studio-candidate-guardrail-copy.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify studio candidate guardrails"
```

Do not push. Do not merge main.
