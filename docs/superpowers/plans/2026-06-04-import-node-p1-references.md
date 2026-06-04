# Import Node P1 Safe References Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline execution in this Claude Code session. User explicitly prohibited subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Confirmed import-node candidate assets become safe, visible creation references in the next-chapter and chapter-drafting flow without mutating formal canon.

**Architecture:** Add a read-only material-reference projection from `import_candidate_assets` into Next Chapter Prep. Freeze those references in `ChapterExecutionContext`, display them in frontend prep/studio panels, and include them in Writer prompt text as non-canon references.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, pytest, React, TypeScript, Vitest, Testing Library.

---

## File Structure

- Modify `backend/app/import_node/schemas.py`: add `ImportMaterialReferenceResponse` schema.
- Modify `backend/app/import_node/service.py`: add `material_references_for_world()` read-only helper.
- Modify `backend/app/narrative_control_center/schemas.py`: add `material_references` to `NextChapterPrepResponse`.
- Modify `backend/app/narrative_control_center/service.py`: include import references in `get_next_chapter_prep()`.
- Modify `backend/app/narrative/schemas.py`: add execution-context material reference schema.
- Modify `backend/app/narrative/service.py`: format references into Writer/Outliner prompts.
- Modify `backend/tests/test_narrative_control_center.py`: add RED test for next prep safe references.
- Modify `backend/tests/test_chapter_execution_context.py`: add RED test for frozen reference prompt.
- Modify `frontend/src/api/types.ts`: add `ImportMaterialReference` and extend types.
- Modify `frontend/src/world/chapterExecutionContext.ts`: carry references into execution context.
- Modify `frontend/src/world/NextChapterPrepPanel.tsx`: show references and safety copy.
- Modify `frontend/src/world/NextChapterPrepPanel.test.tsx`: add RED test for panel and callback.
- Modify `frontend/src/studio/StudioPage.tsx`: show frozen reference count and safety copy.
- Modify `frontend/src/studio/StudioPage.test.tsx`: add RED test for studio copy if existing test structure supports it.

---

### Task 1: Backend safe material references in Next Chapter Prep

**Files:**
- Modify: `backend/tests/test_narrative_control_center.py`
- Modify: `backend/app/import_node/schemas.py`
- Modify: `backend/app/import_node/service.py`
- Modify: `backend/app/narrative_control_center/schemas.py`
- Modify: `backend/app/narrative_control_center/service.py`

- [ ] **Step 1: Write failing backend test**

Add a test that imports material, confirms candidates, calls `/worlds/{world_id}/next-chapter-prep`, and expects material references.

- [ ] **Step 2: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_narrative_control_center.py::test_next_chapter_prep_surfaces_imported_candidates_as_safe_material_references -v
```

Expected: FAIL because `material_references` is missing.

- [ ] **Step 3: Implement minimal backend projection**

Add a read-only helper that joins candidate assets with import batches, limits to recent candidates, and returns safe references. Include the result in Next Chapter Prep.

- [ ] **Step 4: Verify GREEN**

Run the same focused pytest command. Expected: PASS.

---

### Task 2: Backend execution context prompt includes non-canon references

**Files:**
- Modify: `backend/tests/test_chapter_execution_context.py`
- Modify: `backend/app/narrative/schemas.py`
- Modify: `backend/app/narrative/service.py`

- [ ] **Step 1: Write failing backend test**

Add a test that sends an execution context containing material references to `/worlds/{world_id}/chapters/draft`, captures Writer messages, and asserts the prompt includes the reference title plus “不是正式 canon”.

- [ ] **Step 2: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_chapter_execution_context.py::test_direct_draft_prompt_includes_import_material_references_as_non_canon -v
```

Expected: FAIL because execution context schema/prompt does not support material references.

- [ ] **Step 3: Implement schema and prompt support**

Add material references to `ChapterExecutionContext`, manual context defaults, and prompt formatting.

- [ ] **Step 4: Verify GREEN**

Run the same focused pytest command. Expected: PASS.

---

### Task 3: Frontend next-chapter panel surfaces references

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/world/chapterExecutionContext.ts`
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`

- [ ] **Step 1: Write failing frontend test**

Extend `NextChapterPrepPanel.test.tsx` so the fixture includes one imported material reference. Assert the panel shows “导入素材参考” and “不会自动改写正式 canon”, and the callback context includes `material_references`.

- [ ] **Step 2: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx
```

Expected: FAIL because reference UI/type path is missing.

- [ ] **Step 3: Implement minimal frontend display and context carry-through**

Add types, copy references into `buildExecutionContextFromPrep`, and show a compact reference section in the panel.

- [ ] **Step 4: Verify GREEN**

Run the same focused Vitest command. Expected: PASS.

---

### Task 4: Frontend Studio shows frozen reference boundary

**Files:**
- Modify: `frontend/src/studio/StudioPage.tsx`
- Modify: `frontend/src/studio/StudioPage.test.tsx`

- [ ] **Step 1: Write failing frontend test**

Add a Studio test fixture with `launchContext.executionContext.material_references`, assert the execution context panel says references are frozen and not canon.

- [ ] **Step 2: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx
```

Expected: FAIL because Studio does not display material reference boundary.

- [ ] **Step 3: Implement minimal Studio display**

Show count/title snippets in `ExecutionContextSummary` and `ExecutionContextSnapshot` without exposing raw IDs as primary copy.

- [ ] **Step 4: Verify GREEN**

Run the same focused Vitest command. Expected: PASS.

---

### Task 5: Verification and commit

**Files:** all changed files.

- [ ] **Step 1: Run backend targeted tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_import_node.py tests/test_narrative_control_center.py tests/test_chapter_execution_context.py tests/test_migrations.py -v
```

- [ ] **Step 2: Run frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx
```

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

- [ ] **Step 4: Run diff whitespace check**

```bash
git -C /opt/WorldSim-Writer diff --check
```

- [ ] **Step 5: Inline self-review**

Check that no path mutates `truth_canon`, increments `world_version`, updates candidate status, or writes events for read-only reference use.

- [ ] **Step 6: Commit without push/merge**

```bash
git -C /opt/WorldSim-Writer add <changed-files>
git -C /opt/WorldSim-Writer commit -m "feat: surface import materials as chapter references"
```
