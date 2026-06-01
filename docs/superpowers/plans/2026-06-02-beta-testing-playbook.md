# Beta Testing Playbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested beta-testing playbook so testers can validate the MVP main flow consistently.

**Architecture:** Root documentation file plus a lightweight pytest regression in existing docs tests. No runtime behavior changes.

**Tech Stack:** Markdown, pytest.

---

### Task 1: Add failing docs regression

**Files:**
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add a test that reads `/opt/WorldSim-Writer/BETA_TESTING.md`.
- [ ] Assert it includes key headings/terms: mock smoke, real LLM smoke, manual main-flow QA, archive/read-only, cleanup, bug report evidence.
- [ ] Run the focused docs test and verify it fails because the file is missing.

### Task 2: Create beta playbook

**Files:**
- Create: `BETA_TESTING.md`

- [ ] Document prerequisites and local setup.
- [ ] Document backend/frontend gates.
- [ ] Document mock smoke and optional real-LLM smoke commands.
- [ ] Document manual main-flow QA and archive/read-only spot checks.
- [ ] Document cleanup and bug-report evidence.

### Task 3: Verify and commit

- [ ] Run focused docs test.
- [ ] Run backend full pytest.
- [ ] Run frontend build.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit relevant files only.
