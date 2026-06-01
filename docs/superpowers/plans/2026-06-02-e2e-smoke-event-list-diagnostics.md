# E2E Smoke Event List Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Report successful events responses missing `items` as malformed events-step responses.

**Architecture:** Reuse `_require_fields` in `backend/scripts/e2e_smoke.py` after the events API call succeeds and before deriving `event_types`.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing events missing-items test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_event_items_for_event_check`.
- [ ] Mock the normal flow through approval, then return events JSON with `summary` but no `items`.
- [ ] Assert `summary['ok'] is False`, `failed_step == 'events'`, `error == 'MISSING_REQUIRED_FIELDS'`, and `missing_fields == ['items']`.
- [ ] Assert no markdown export request is made after malformed events.
- [ ] Run the focused test and confirm RED because events currently defaults missing `items` to an empty list.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_event_items_for_event_check -q
```

### Task 2: Require event items

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add `_require_fields(summary, 'events', events, ['items'])` immediately after events `_step_json` succeeds.
- [ ] Return the summary if validation fails.
- [ ] Keep existing `chapter_approved_seen` semantic check unchanged.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Verify and commit

**Files:**
- No `BETA_TESTING.md` update required because it already documents `MISSING_REQUIRED_FIELDS`, `missing_fields`, and the `chapter_approved` event criterion.

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
