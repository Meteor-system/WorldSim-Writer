# Continuous Smoke Approval Gate Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add second-chapter approval preview/readiness/consistency diagnostics to the optional continuous smoke JSON summary.

**Architecture:** Reuse values already computed inside `backend/scripts/e2e_smoke.py` during the `E2E_CONTINUOUS_CHAPTERS=1` path. Extend only the smoke summary and beta runbook; do not change API routes, narrative services, model calls, or approval behavior.

**Tech Stack:** Python, pytest, httpx transport tests.

---

## File Structure

- Modify `backend/tests/test_e2e_scripts.py`: add failing assertions for new continuous smoke diagnostics.
- Modify `backend/scripts/e2e_smoke.py`: add diagnostic fields to `checks.continuous_chapters`.
- Modify `BETA_TESTING.md`: document expected values for the new diagnostics.
- Create `docs/superpowers/specs/2026-06-09-continuous-smoke-approval-gate-diagnostics-design.md`: design note.
- Create `docs/superpowers/plans/2026-06-09-continuous-smoke-approval-gate-diagnostics.md`: this plan.

---

### Task 1: Add failing continuous smoke diagnostics assertions

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] **Step 1: Add assertions**

In `test_e2e_smoke_script_optionally_checks_continuous_second_chapter_and_stale_draft`, after the existing `fresh_priority_foreshadow_count` / world-version checkpoint assertions, add:

```python
assert summary['checks']['continuous_chapters']['second_preview_version_conflict'] is False
assert summary['checks']['continuous_chapters']['second_proposed_change_count'] == 2
assert summary['checks']['continuous_chapters']['second_readiness_status'] == 'ready'
assert summary['checks']['continuous_chapters']['second_readiness_blocked'] is False
assert summary['checks']['continuous_chapters']['second_consistency_status'] == 'clear'
assert summary['checks']['continuous_chapters']['second_consistency_blocked'] is False
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_optionally_checks_continuous_second_chapter_and_stale_draft -q'
```

Expected: fail with `KeyError` for one of the new diagnostics.

---

### Task 2: Add smoke summary fields

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] **Step 1: Add preview/readiness/consistency fields**

Inside the existing `summary['checks']['continuous_chapters'] = { ... }` dictionary, add:

```python
'second_preview_version_conflict': second_preview.get('version_conflict'),
'second_proposed_change_count': second_proposed_change_count,
'second_readiness_status': second_readiness.get('status'),
'second_readiness_blocked': second_readiness_blocked,
'second_consistency_status': second_consistency_summary.get('status'),
'second_consistency_blocked': second_consistency_blocked,
```

- [ ] **Step 2: Run GREEN**

Run the focused pytest command again and expect pass.

---

### Task 3: Update beta runbook and verify

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] **Step 1: Document diagnostics**

In the continuous smoke pass criteria, add that:

- `second_preview_version_conflict` should be `false`.
- `second_proposed_change_count` should be greater than `0`.
- `second_readiness_status` should be `ready` or `needs_review` and `second_readiness_blocked` should be `false`.
- `second_consistency_status` should be `clear` or `needs_review` and `second_consistency_blocked` should be `false`.

- [ ] **Step 2: Run relevant tests**

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_e2e_scripts.py -q'
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_pipeline.py tests/test_e2e_scripts.py -q'
```

- [ ] **Step 3: Diff checks and commit**

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add backend/scripts/e2e_smoke.py backend/tests/test_e2e_scripts.py BETA_TESTING.md docs/superpowers/specs/2026-06-09-continuous-smoke-approval-gate-diagnostics-design.md docs/superpowers/plans/2026-06-09-continuous-smoke-approval-gate-diagnostics.md
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "test: add continuous smoke approval diagnostics"
```

Do not push or merge.
