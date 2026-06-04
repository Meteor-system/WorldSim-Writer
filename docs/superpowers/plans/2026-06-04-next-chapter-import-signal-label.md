# Next Chapter Import Signal Label Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify the next-chapter prep imported-material source signal as a candidate material reference.

**Architecture:** Frontend-only copy update in `NextChapterPrepPanel.tsx`. Change the `import_material_reference` signal label only; keep reference details, context payloads, buttons, prep behavior, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
  - Add the import-material source signal to the fixture.
  - Expect the safer signal label and reject the raw slug.
  - Preserve raw ID/enum hiding and context payload assertions.
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`
  - Replace the visible signal label for `import_material_reference`.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Next-chapter prep labels import source signal as candidate reference

**Files:**
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`

- [ ] **Step 1: Write the failing test**

In the `prep` fixture, change:

```ts
source_signals: ['character_arc_progression_hint', 'story_arc'],
```

To:

```ts
source_signals: ['character_arc_progression_hint', 'story_arc', 'import_material_reference'],
```

In `renders next chapter prep signals and uses suggested goal callback`, add these assertions near the existing source-signal label assertions:

```ts
expect(screen.getByText('候选素材参考')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('import_material_reference');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx -t "renders next chapter prep signals"
```

Expected: FAIL because production still renders `导入素材参考` for the import source signal.

- [ ] **Step 3: Write minimal implementation**

In `NextChapterPrepPanel.tsx`, change:

```ts
import_material_reference: '导入素材参考',
```

To:

```ts
import_material_reference: '候选素材参考',
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx -t "renders next chapter prep signals"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for clearer candidate-reference signal wording, unchanged context payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-next-chapter-import-signal-label-design.md docs/superpowers/plans/2026-06-04-next-chapter-import-signal-label.md frontend/src/world/NextChapterPrepPanel.tsx frontend/src/world/NextChapterPrepPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify import source signal label"
```

Do not push. Do not merge main.
