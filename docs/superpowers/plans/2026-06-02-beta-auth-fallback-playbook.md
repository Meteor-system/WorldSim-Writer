# Beta Auth Fallback Playbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Document smoke auth fallback diagnostics so beta testers can distinguish fresh registration from repeated-email login.

**Architecture:** Add a documentation regression test for concrete smoke auth summary terms, then update `BETA_TESTING.md` pass criteria and diagnostic guidance.

**Tech Stack:** Python, pytest, Markdown docs.

---

### Task 1: Add failing docs regression terms

**Files:**
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `checks.register`, `checks.login`, and `E2E_EMAIL` to the `required_terms` list in `test_beta_testing_playbook_documents_main_flow_smoke_and_reporting`.
- [ ] Run the focused docs test and confirm RED because the playbook does not yet document concrete auth fallback summary terms.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
```

### Task 2: Document auth fallback interpretation

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] In mock smoke pass criteria, add a bullet explaining that auth evidence appears as either `checks.register` or `checks.login`.
- [ ] Explain that `checks.login` is expected when `E2E_EMAIL` reuses an existing smoke account or a previous run already created that email before cleanup.
- [ ] In real-LLM diagnostics, keep the existing failure-field guidance and add that `failed_step: "login"` identifies fallback-login response problems.
- [ ] Rerun the focused docs test and confirm GREEN.

### Task 3: Verify and commit

**Files:**
- No production code changes expected.

- [ ] Run `backend/tests/test_event_docs.py`.
- [ ] Run `backend/tests/test_e2e_scripts.py` to ensure smoke diagnostics remain covered.
- [ ] Run full backend tests.
- [ ] Run frontend tests/build only if frontend files change; otherwise skip and state why.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
