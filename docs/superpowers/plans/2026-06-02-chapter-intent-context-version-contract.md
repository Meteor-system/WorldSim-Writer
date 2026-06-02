# Chapter Intent Context Version Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Reject stale provided chapter execution contexts before creating chapter sessions or direct drafts.

**Architecture:** Add a small validation inside `backend/app/narrative/service.py::normalize_execution_context()` after provided contexts are normalized and the goal is overwritten. If a provided context's `source_world_version` differs from the current world version, raise `HTTPException(409, detail='WORLD_VERSION_MISMATCH')`. Keep backend-generated manual contexts unchanged.

**Tech Stack:** FastAPI, SQLAlchemy, pytest.

---

### Task 1: Add failing stale context test for chapter session creation

**Files:**
- Modify: `backend/tests/test_chapter_execution_context.py`

- [ ] Add `test_create_chapter_rejects_stale_execution_context` after the existing manual-context test.
- [ ] Register/create a sample world at world version 1.
- [ ] Build `context = sample_execution_context(source_world_version=0)`.
- [ ] POST `/worlds/{world_id}/chapters` with the stale context.
- [ ] Assert:

```python
assert response.status_code == 409
assert response.json()['detail'] == 'WORLD_VERSION_MISMATCH'
assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == 0
```

- [ ] Run the focused test and confirm RED because stale context is currently accepted.

### Task 2: Add failing stale context test for direct draft creation

**Files:**
- Modify: `backend/tests/test_chapter_execution_context.py`

- [ ] Add `test_direct_draft_rejects_stale_execution_context_before_model_call` near the direct draft context test.
- [ ] Register/create a sample world at world version 1.
- [ ] Build `context = sample_execution_context(source_world_version=0)`.
- [ ] Patch `narrative_service.LLMClient` with `CapturingLLMClient`.
- [ ] POST `/worlds/{world_id}/chapters/draft` with the stale context.
- [ ] Assert:

```python
assert response.status_code == 409
assert response.json()['detail'] == 'WORLD_VERSION_MISMATCH'
assert llm.messages == []
```

- [ ] Run the focused test and confirm RED because stale context currently reaches the model.

### Task 3: Implement context version validation

**Files:**
- Modify: `backend/app/narrative/service.py`
- Modify: `backend/tests/test_chapter_execution_context.py`

- [ ] Change `sample_execution_context()` to accept `source_world_version: int = 1` and use that value.
- [ ] In `normalize_execution_context()`, track whether a context was provided.
- [ ] After `context['goal'] = chapter_goal`, add:

```python
if context_provided and context.get('source_world_version') != world.world_version:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='WORLD_VERSION_MISMATCH')
```

- [ ] Rerun focused stale-context tests and confirm GREEN.
- [ ] Rerun `backend/tests/test_chapter_execution_context.py` and confirm GREEN.

### Task 4: Verify and commit

**Files:**
- Backend narrative service, execution-context tests, and planning docs only.

- [ ] Run focused stale-context tests.
- [ ] Run all chapter execution context tests.
- [ ] Run relevant narrative approval tests.
- [ ] Run frontend build only if frontend files changed; otherwise skip.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/*` and `backend/worldsim-dev.db`.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current feature branch.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_chapter_execution_context.py::test_create_chapter_rejects_stale_execution_context tests/test_chapter_execution_context.py::test_direct_draft_rejects_stale_execution_context_before_model_call -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_chapter_execution_context.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_approval.py -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
