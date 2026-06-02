# E2E Smoke Overview World Version Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate post-approval world-version advancement from world overview instead of `ChapterResponse.approved_version`.

**Architecture:** Keep the existing smoke sequence. The `approve` step validates response shape/status and records approval metadata. The `overview` step becomes the authoritative world-version increment check by comparing `overview.world_version` with `initial_world_version + 1`.

**Tech Stack:** Python, httpx, pytest, Markdown.

---

## File map

- Modify `backend/tests/test_e2e_scripts.py` — add/update RED/GREEN regression tests for approval version vs world version.
- Modify `backend/scripts/e2e_smoke.py` — move world-version increment validation to overview.
- Modify `BETA_TESTING.md` — document the corrected smoke contract.
- Modify `backend/tests/test_event_docs.py` — require beta docs wording.
- Create `docs/superpowers/specs/2026-06-02-e2e-smoke-overview-world-version-contract-design.md` — design record.
- Create `docs/superpowers/plans/2026-06-02-e2e-smoke-overview-world-version-contract.md` — this implementation plan.

### Task 1: Add failing real-LLM regression

- [ ] Add a test where approval returns `approved_version: 1`, overview returns `world_version: 2`, and the rest of the smoke succeeds.
- [ ] Assert `summary['ok'] is True`.
- [ ] Assert `checks.approve.approved_version == 1` and `checks.approve.world_version_validation_source == 'overview'`.
- [ ] Assert `checks.overview.expected_world_version == 2` and `checks.overview.world_version_incremented is True`.
- [ ] Run the focused test and verify RED because current code fails at `approve` with `WORLD_VERSION_NOT_INCREMENTED`.

### Task 2: Implement overview-based world-version validation

- [ ] Remove the `approve`-step comparison between `approved_version` and `initial_world_version + 1`.
- [ ] Keep `checks.approve.status`, `checks.approve.approved_version`, `checks.approve.expected_world_version_after`, and add `world_version_validation_source: 'overview'`.
- [ ] After overview, compare `overview.world_version` to `expected_world_version_after`.
- [ ] Store `checks.overview.world_version_incremented` and keep `checks.overview.world_version_matches_approval` as a backward-compatible alias for now.
- [ ] Report stale world-version failures from `failed_step: 'overview'` with `error: 'WORLD_VERSION_NOT_INCREMENTED'`.

### Task 3: Update docs contract

- [ ] Update `BETA_TESTING.md` approve/overview pass criteria to say approval response `approved_version` is metadata and world-version increment is validated via overview.
- [ ] Update docs coverage terms for `checks.approve.world_version_validation_source`, `checks.overview.world_version_incremented`, and approval response metadata wording.

### Task 4: Verify and commit

- [ ] Run focused tests for the new regression and stale-overview failure.
- [ ] Run `tests/test_e2e_scripts.py`.
- [ ] Run `tests/test_event_docs.py`.
- [ ] Run full backend pytest.
- [ ] Run the user-provided real-LLM smoke command.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit without pushing or merging.
