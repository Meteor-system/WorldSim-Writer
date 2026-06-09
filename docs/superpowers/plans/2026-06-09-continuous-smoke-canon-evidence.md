# Continuous Smoke Canon Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Story Bible/canon evidence diagnostics to optional continuous two-chapter smoke output.

**Architecture:** Reuse the new next-chapter prep response fields already returned by the backend. Extend only smoke validation/summary and beta runbook text; do not change API routes, generation, approval, or frontend behavior.

**Tech Stack:** Python, pytest, httpx transport tests, Markdown docs.

---

## File Structure

- Modify `backend/tests/test_e2e_scripts.py`: fake prep responses include canon evidence; continuous smoke test asserts new summary fields.
- Modify `backend/scripts/e2e_smoke.py`: require canon fields and report match/version diagnostics.
- Modify `BETA_TESTING.md`: document expected continuous-smoke canon evidence.
- Create this plan and the matching design doc.

---

### Task 1: Add failing smoke assertions

- [ ] Update `next_chapter_prep_response` in `backend/tests/test_e2e_scripts.py` to accept and return `truth_canon_version` and `truth_canon_excerpt`.

- [ ] In `test_e2e_smoke_script_optionally_checks_continuous_second_chapter_and_stale_draft`, build:

```python
second_prep = next_chapter_prep_response(
    world_version=3,
    truth_canon_excerpt=module.SECOND_CHAPTER_CANON,
    truth_canon_version=2,
).json()
fresh_second_prep = next_chapter_prep_response(
    world_version=4,
    previous_summary='第二章重新准备前仍承接第一章摘要。',
    truth_canon_excerpt=module.STALE_DRAFT_CANON,
    truth_canon_version=3,
).json()
```

- [ ] Add assertions:

```python
assert summary['checks']['continuous_chapters']['prep_truth_canon_version'] == 2
assert summary['checks']['continuous_chapters']['prep_truth_canon_excerpt_matches'] is True
assert summary['checks']['continuous_chapters']['fresh_prep_truth_canon_version'] == 3
assert summary['checks']['continuous_chapters']['fresh_prep_truth_canon_excerpt_matches'] is True
```

- [ ] Run RED:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_optionally_checks_continuous_second_chapter_and_stale_draft -q
```

Expected: fail with missing `prep_truth_canon_version` or related summary key.

---

### Task 2: Add smoke validation and summary fields

- [ ] In `backend/scripts/e2e_smoke.py`, require `truth_canon_version` and `truth_canon_excerpt` for both `next_chapter_prep` and `fresh_next_chapter_prep`.

- [ ] Validate field types with existing helpers:

```python
_require_int_fields(..., ['world_version', 'next_chapter_number', 'truth_canon_version'])
_require_string_fields(..., ['truth_canon_excerpt'])
```

- [ ] Compute match booleans:

```python
prep_truth_canon_excerpt_matches = prep.get('truth_canon_excerpt') == SECOND_CHAPTER_CANON
fresh_prep_truth_canon_excerpt_matches = fresh_prep.get('truth_canon_excerpt') == STALE_DRAFT_CANON
```

- [ ] If the excerpt match is false or the prep `truth_canon_version` does not equal the preceding canon-update response's `truth_canon_version`, stop with `CANON_EVIDENCE_NOT_CURRENT` on the relevant prep step.

- [ ] Add summary fields:

```python
'prep_truth_canon_version': prep.get('truth_canon_version'),
'prep_truth_canon_excerpt_matches': prep_truth_canon_excerpt_matches,
'fresh_prep_truth_canon_version': fresh_prep.get('truth_canon_version'),
'fresh_prep_truth_canon_excerpt_matches': fresh_prep_truth_canon_excerpt_matches,
```

- [ ] Run GREEN focused pytest.

---

### Task 3: Docs, verification, commit

- [ ] Update `BETA_TESTING.md` continuous smoke pass criteria to mention the new canon-evidence diagnostics and `CANON_EVIDENCE_NOT_CURRENT` failure.

- [ ] Run related backend tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py tests/test_narrative_pipeline.py tests/test_narrative_control_center.py -q
```

- [ ] Run full backend tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
```

- [ ] If frontend was not touched, skip frontend tests/build and state that explicitly; otherwise run relevant frontend tests/build.

- [ ] Run diff checks and commit only:

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add backend/scripts/e2e_smoke.py backend/tests/test_e2e_scripts.py BETA_TESTING.md docs/superpowers/specs/2026-06-09-continuous-smoke-canon-evidence-design.md docs/superpowers/plans/2026-06-09-continuous-smoke-canon-evidence.md
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "test: add continuous smoke canon evidence"
```

Do not push or merge.
