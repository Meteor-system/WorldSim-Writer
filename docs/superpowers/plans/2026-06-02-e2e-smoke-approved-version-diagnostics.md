# E2E Smoke Approved Version Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Report successful approval responses missing `approved_version` as malformed approval-step responses.

**Architecture:** Reuse the existing `_require_fields` helper in `backend/scripts/e2e_smoke.py` immediately after the approval API call succeeds and before computing `world_version_incremented`.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing approval missing-version test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_approved_version_after_approval`.
- [ ] Mock the normal flow through approval, but make the approval response `{'id': 20, 'status': 'approved'}` with no `approved_version`.
- [ ] Assert `summary['ok'] is False`, `failed_step == 'approve'`, `error == 'MISSING_REQUIRED_FIELDS'`, and `missing_fields == ['approved_version']`.
- [ ] Assert no events/export requests are made after malformed approval.
- [ ] Run the focused test and confirm RED because approval currently treats `approved_version` as optional.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_approved_version_after_approval -q
```

### Task 2: Require approved_version after approval

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add `_require_fields(summary, 'approve', approved, ['approved_version'])` immediately after the approval `_step_json` success check.
- [ ] Return the summary if validation fails.
- [ ] Keep existing `approved.get('status') == 'approved'` final `ok` check unchanged.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Verify and commit

**Files:**
- No `BETA_TESTING.md` update required because it already documents `MISSING_REQUIRED_FIELDS` and `missing_fields`.

- [ ] Run related smoke script tests.
- [ ] Run full backend tests.
- [ ] Run frontend tests/build because the user requested related tests/build and no frontend changes are expected.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer/frontend && npm run test -- --run
cd /opt/WorldSim-Writer/frontend && npm run build
cd /opt/WorldSim-Writer && git diff --check
```
