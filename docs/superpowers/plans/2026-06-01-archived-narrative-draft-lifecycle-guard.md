# Archived Narrative Draft Lifecycle Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and dynamic workflows, so execute inline with strict TDD.

**Goal:** Reject narrative draft lifecycle mutations while a world is archived.

**Architecture:** Keep archive enforcement inside `app.narrative.service` near the state mutations. Reuse `_ensure_world_is_active()` and add a small world lookup helper for chapter-scoped services.

**Tech Stack:** FastAPI, SQLAlchemy, pytest.

---

## File Structure

- Modify: `backend/tests/test_narrative_pipeline.py`
  - Add archived pipeline mutation guard test for outline/write/critique.
- Modify: `backend/tests/test_narrative_draft_versioning.py`
  - Add archived draft edit/stash/paragraph/revise guard test.
- Modify: `backend/tests/test_critic_reports.py`
  - Add archived critic report generation guard test.
- Modify: `backend/tests/test_character_arc_reports.py`
  - Add archived character arc report generation guard test.
- Modify: `backend/app/narrative/service.py`
  - Guard pipeline, draft lifecycle, and report-generation mutation services.
- Create: `docs/superpowers/specs/2026-06-01-archived-narrative-draft-lifecycle-guard-design.md`
  - Design spec for this MVP.
- Create: `docs/superpowers/plans/2026-06-01-archived-narrative-draft-lifecycle-guard.md`
  - This implementation plan.

---

### Task 1: Add RED tests

- [ ] **Step 1: Add pipeline mutation test**

In `backend/tests/test_narrative_pipeline.py`, add a test that creates a chapter while active, archives the world, then asserts outline/write/critique all return `409 WORLD_ARCHIVED`.

- [ ] **Step 2: Add draft lifecycle test**

In `backend/tests/test_narrative_draft_versioning.py`, add a test that creates a reviewing draft while active, archives the world, then asserts edit/stash/paragraph/revise all return `409 WORLD_ARCHIVED`, while the chapter remains at draft version 1.

- [ ] **Step 3: Add report generation tests**

In `backend/tests/test_critic_reports.py` and `backend/tests/test_character_arc_reports.py`, add one test each asserting archived report-generation POST endpoints return `409 WORLD_ARCHIVED`.

- [ ] **Step 4: Run targeted RED tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_pipeline.py::test_archived_world_rejects_pipeline_mutations tests/test_narrative_draft_versioning.py::test_archived_world_rejects_draft_lifecycle_mutations tests/test_critic_reports.py::test_archived_world_rejects_critic_report_generation tests/test_character_arc_reports.py::test_archived_world_rejects_character_arc_report_generation -q
```

Expected: fail because archived mutation endpoints still mutate or return older precondition errors.

---

### Task 2: Implement minimal GREEN

- [ ] **Step 1: Add `_world_for_chapter()` helper**

In `backend/app/narrative/service.py`, add:

```python
def _world_for_chapter(db: Session, chapter: Chapter) -> World:
    world = db.get(World, chapter.world_id)
    assert world is not None
    return world
```

- [ ] **Step 2: Guard pipeline/report mutations**

In `generate_chapter_outline()`, `write_chapter_from_outline()`, `critique_chapter()`, `generate_critic_report()`, and `generate_character_arc_report()`, load the chapter world and call `_ensure_world_is_active(world)` before mutating chapter fields or calling the model.

- [ ] **Step 3: Guard draft lifecycle mutations**

In `edit_chapter_draft()`, `stash_chapter_draft()`, `revise_chapter_draft()`, and `revise_chapter_paragraph()`, load the chapter world and call `_ensure_world_is_active(world)` before creating a new draft version or calling the model.

- [ ] **Step 4: Run targeted GREEN tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_pipeline.py::test_archived_world_rejects_pipeline_mutations tests/test_narrative_draft_versioning.py::test_archived_world_rejects_draft_lifecycle_mutations tests/test_critic_reports.py::test_archived_world_rejects_critic_report_generation tests/test_character_arc_reports.py::test_archived_world_rejects_character_arc_report_generation -q
```

Expected: pass.

---

### Task 3: Verify and commit

- [ ] **Step 1: Run relevant backend tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_pipeline.py tests/test_narrative_draft_versioning.py tests/test_critic_reports.py tests/test_character_arc_reports.py -q
```

Expected: pass.

- [ ] **Step 2: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Run relevant frontend archive tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: pass.

- [ ] **Step 4: Run diff check and status review**

```bash
cd /opt/WorldSim-Writer && git diff --check && git status --short && git diff --stat
```

Expected: no whitespace errors; do not stage unrelated `.hermes/plans/*` or `backend/worldsim-dev.db`.

- [ ] **Step 5: Commit relevant files only**

```bash
cd /opt/WorldSim-Writer && git add backend/app/narrative/service.py backend/tests/test_narrative_pipeline.py backend/tests/test_narrative_draft_versioning.py backend/tests/test_critic_reports.py backend/tests/test_character_arc_reports.py docs/superpowers/specs/2026-06-01-archived-narrative-draft-lifecycle-guard-design.md docs/superpowers/plans/2026-06-01-archived-narrative-draft-lifecycle-guard.md && git commit -m "fix: reject archived draft lifecycle writes"
```

Expected: commit succeeds. Do not push and do not merge.
