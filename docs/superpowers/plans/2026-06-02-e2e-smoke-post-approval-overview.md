# E2E Smoke Post-Approval Overview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Add a post-approval world overview check to the smoke script so beta smoke proves the user-facing overview reflects the approved chapter.

**Architecture:** Extend `backend/scripts/e2e_smoke.py::run_smoke()` after approval response validation and before event/export checks. Reuse existing response validation helpers for fields, integer fields, and list-of-dicts projection collections. Document the new diagnostic in `BETA_TESTING.md` and enforce it via `backend/tests/test_event_docs.py`.

**Tech Stack:** Python, httpx, pytest, FastAPI smoke helper script.

---

### Task 1: Add failing smoke tests for overview verification

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Update `test_e2e_smoke_script_runs_api_flow_and_returns_json_summary` so the response sequence includes overview JSON after approval and before events:

```python
json_response({'world_version': 2, 'approved_chapter_count': 1, 'characters': [{'id': 1}], 'foreshadows': [{'id': 1}]}),
```

- [ ] Assert `summary['checks']['overview']['world_version_matches_approval'] is True` and `summary['checks']['overview']['approved_chapter_count_incremented'] is True`.
- [ ] Update the expected request path list to include `/worlds/10/overview` between approve and events.
- [ ] Add `test_e2e_smoke_script_fails_when_post_approval_overview_is_stale` with approval returning `approved_version: 2` but overview returning `world_version: 1`.
- [ ] Assert the smoke stops at `failed_step == 'overview'` with `error == 'OVERVIEW_WORLD_VERSION_NOT_UPDATED'` and does not call events/export.
- [ ] Run the focused tests and confirm RED because the smoke script does not fetch overview yet.

### Task 2: Implement post-approval overview check

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After approval status/version checks, call:

```python
overview = _step_json(summary, 'overview', lambda: client.get(f'/worlds/{world_id}/overview', headers=headers))
```

- [ ] Require `world_version`, `approved_chapter_count`, `characters`, and `foreshadows`.
- [ ] Validate `world_version` and `approved_chapter_count` as ints; validate `characters` and `foreshadows` as list-of-dicts.
- [ ] Build `checks.overview` with counts and booleans.
- [ ] Stop with `OVERVIEW_WORLD_VERSION_NOT_UPDATED`, `OVERVIEW_APPROVED_CHAPTER_MISSING`, or `OVERVIEW_PROJECTION_EMPTY` when those checks fail.
- [ ] Include the overview booleans and non-empty projection requirements in final `summary['ok']`.
- [ ] Rerun focused smoke tests and confirm GREEN.

### Task 3: Document the new diagnostic

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `OVERVIEW_WORLD_VERSION_NOT_UPDATED`, `OVERVIEW_APPROVED_CHAPTER_MISSING`, `OVERVIEW_PROJECTION_EMPTY`, `checks.overview.world_version_matches_approval`, and `checks.overview.approved_chapter_count_incremented` to the beta playbook pass criteria.
- [ ] Add those terms to the documentation coverage test.
- [ ] Run `backend/tests/test_event_docs.py` and confirm GREEN.

### Task 4: Verify and commit

**Files:**
- Backend smoke script, smoke tests, beta docs, docs coverage test, and planning docs only.

- [ ] Run focused smoke tests for happy path and stale overview.
- [ ] Run all `backend/tests/test_e2e_scripts.py`.
- [ ] Run `backend/tests/test_event_docs.py`.
- [ ] Run frontend tests/build only if frontend files changed; otherwise skip.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/*` and `backend/worldsim-dev.db`.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current feature branch.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_runs_api_flow_and_returns_json_summary tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_post_approval_overview_is_stale -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
