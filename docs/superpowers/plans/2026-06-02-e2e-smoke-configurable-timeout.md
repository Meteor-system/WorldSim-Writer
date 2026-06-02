# E2E Smoke Configurable Timeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Allow real-LLM smoke runs to increase the HTTP client timeout without editing the smoke script.

**Architecture:** Add a tiny timeout parser in `backend/scripts/e2e_smoke.py`, use it when constructing the owned `httpx.Client`, and report the chosen value in the summary. Document the environment variable in the beta playbook.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing timeout parser tests

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_uses_default_timeout_seconds`.
- [ ] Add `test_e2e_smoke_script_reads_custom_timeout_seconds`.
- [ ] Add `test_e2e_smoke_script_falls_back_for_invalid_timeout_seconds`.
- [ ] These tests should call `module._timeout_seconds()` directly for focused coverage.
- [ ] Assert default is `60.0` when `E2E_TIMEOUT_SECONDS` is unset.
- [ ] Assert custom value is parsed as a float when `E2E_TIMEOUT_SECONDS=180`.
- [ ] Assert invalid values such as `0`, `-1`, and `abc` return `60.0`.
- [ ] Run the focused tests and confirm RED because `_timeout_seconds()` does not exist yet.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_uses_default_timeout_seconds \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_reads_custom_timeout_seconds \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_falls_back_for_invalid_timeout_seconds -q
```

### Task 2: Add failing client-construction timeout test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_passes_timeout_to_owned_client`.
- [ ] Monkeypatch `module.httpx.Client` with a fake factory that captures the `timeout` keyword and raises a controlled `RuntimeError` from `get('/health')`.
- [ ] Set `BASE_URL=https://worldsim.test` and `E2E_TIMEOUT_SECONDS=180`.
- [ ] Call `module.run_smoke()` without injecting a client.
- [ ] Assert captured timeout is `180.0`.
- [ ] Assert summary includes `timeout_seconds == 180.0` and `failed_step == 'health'`.
- [ ] Assert the fake client was closed.
- [ ] Run the focused test and confirm RED because the script currently passes `60.0` directly.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_passes_timeout_to_owned_client -q
```

### Task 3: Implement configurable timeout

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add constant `DEFAULT_TIMEOUT_SECONDS = 60.0`.
- [ ] Add helper:

```python
def _timeout_seconds() -> float:
    raw_value = os.getenv('E2E_TIMEOUT_SECONDS', '').strip()
    if not raw_value:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = float(raw_value)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    if timeout <= 0:
        return DEFAULT_TIMEOUT_SECONDS
    return timeout
```

- [ ] In `run_smoke()`, compute `timeout_seconds = _timeout_seconds()` before client creation.
- [ ] Use `httpx.Client(base_url=base_url, timeout=timeout_seconds)` when the script owns the client.
- [ ] Add `'timeout_seconds': timeout_seconds` to the summary.
- [ ] Rerun focused timeout tests and confirm GREEN.
- [ ] Rerun all smoke-script tests.

### Task 4: Document the timeout override

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add docs regression term `E2E_TIMEOUT_SECONDS`.
- [ ] Run the focused docs test and confirm RED if the playbook lacks the term.
- [ ] Update the real-LLM smoke section to mention `E2E_TIMEOUT_SECONDS=180` for slower providers or local model queues.
- [ ] Rerun the focused docs test and confirm GREEN.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
```

### Task 5: Verify and commit

**Files:**
- No frontend changes expected.

- [ ] Run `backend/tests/test_e2e_scripts.py`.
- [ ] Run `backend/tests/test_event_docs.py`.
- [ ] Run full backend tests.
- [ ] Skip frontend tests/build unless frontend files changed; state that no frontend files changed.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only; do not stage `.hermes/plans/*` or `backend/worldsim-dev.db`.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
