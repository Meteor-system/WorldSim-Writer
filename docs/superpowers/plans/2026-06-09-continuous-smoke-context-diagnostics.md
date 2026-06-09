# Continuous Smoke Context Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add richer optional two-chapter smoke diagnostics so beta testers can see whether chapter 2 and regenerated chapter 2 used the intended execution context.

**Architecture:** Extend the existing continuous branch in `backend/scripts/e2e_smoke.py` after it validates second/fresh draft execution contexts. Keep all HTTP calls, API expectations, and default smoke behavior unchanged. Cover the behavior with the existing script-level `httpx` transport test.

**Tech Stack:** Python 3.13, httpx transport tests, pytest.

---

## File Structure

- Modify `backend/tests/test_e2e_scripts.py`: add failing assertions to the existing continuous smoke test.
- Modify `backend/scripts/e2e_smoke.py`: add diagnostic fields to `checks.continuous_chapters`.
- Modify `BETA_TESTING.md`: mention the new diagnostic fields in continuous smoke pass/failure guidance.
- Create `docs/superpowers/specs/2026-06-09-continuous-smoke-context-diagnostics-design.md`: design note.
- Create `docs/superpowers/plans/2026-06-09-continuous-smoke-context-diagnostics.md`: this plan.

---

### Task 1: Add failing smoke diagnostics assertions

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] **Step 1: Add assertions**

In `test_e2e_smoke_script_optionally_checks_continuous_second_chapter_and_stale_draft`, after the existing continuous check assertions, assert these fields:

```python
assert summary['checks']['continuous_chapters']['second_draft_source_world_version'] == 3
assert summary['checks']['continuous_chapters']['second_context_goal_matches'] is True
assert summary['checks']['continuous_chapters']['second_previous_chapter_summary_present'] is True
assert summary['checks']['continuous_chapters']['second_priority_foreshadow_count'] == 1
assert summary['checks']['continuous_chapters']['stale_world_version'] == 4
assert summary['checks']['continuous_chapters']['fresh_prep_world_version'] == 4
assert summary['checks']['continuous_chapters']['fresh_context_goal_matches'] is True
assert summary['checks']['continuous_chapters']['fresh_previous_chapter_summary_present'] is True
assert summary['checks']['continuous_chapters']['fresh_priority_foreshadow_count'] == 1
assert summary['checks']['continuous_chapters']['expected_second_world_version_after'] == 5
```

- [ ] **Step 2: Run RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 python -m pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_optionally_checks_continuous_second_chapter_and_stale_draft -q
```

Expected: fail with `KeyError` for a newly expected diagnostic field.

---

### Task 2: Implement diagnostics

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] **Step 1: Compute second context diagnostics**

After `second_execution_context` is loaded and validated, compute:

```python
second_priority_foreshadow_count = len(second_execution_context.get('priority_foreshadows') or [])
second_context_goal_matches = second_execution_context.get('goal') == SECOND_CHAPTER_GOAL
```

- [ ] **Step 2: Compute fresh context diagnostics**

After `fresh_execution_context` is loaded and validated, compute:

```python
fresh_priority_foreshadow_count = len(fresh_execution_context.get('priority_foreshadows') or [])
fresh_context_goal_matches = fresh_execution_context.get('goal') == FRESH_SECOND_CHAPTER_GOAL
```

- [ ] **Step 3: Add fields to summary**

Extend `summary['checks']['continuous_chapters']` with the fields from Task 1. Keep existing keys unchanged.

- [ ] **Step 4: Run GREEN**

Run the focused test again and expect pass.

---

### Task 3: Update runbook text

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] **Step 1: Update continuous smoke guidance**

In section 3, update the continuous smoke bullet to mention the new second/fresh context diagnostics and expected world-version fields.

---

### Task 4: Verify and commit

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run related tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 python -m pytest tests/test_e2e_scripts.py -q
```

- [ ] **Step 2: Run full backend tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 python -m pytest -q
```

- [ ] **Step 3: Run diff checks and commit**

```bash
cd /opt/WorldSim-Writer
git diff --check
git add backend/scripts/e2e_smoke.py backend/tests/test_e2e_scripts.py BETA_TESTING.md docs/superpowers/specs/2026-06-09-continuous-smoke-context-diagnostics-design.md docs/superpowers/plans/2026-06-09-continuous-smoke-context-diagnostics.md
git diff --cached --check
git commit -m "test: enrich continuous smoke diagnostics"
```

Do not push or merge.
