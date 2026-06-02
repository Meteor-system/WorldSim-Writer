# E2E Smoke Markdown Export Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Report successful markdown export responses missing documented archive fields as malformed export-step responses.

**Architecture:** Reuse `_require_fields` in `backend/scripts/e2e_smoke.py` after the markdown export API call succeeds and before deriving export checks.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing markdown export missing-field test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_markdown_export_archive_fields`.
- [ ] Mock the normal flow through events, then return markdown export JSON missing `archive_base64` while including the other archive fields.
- [ ] Assert `summary['ok'] is False`, `failed_step == 'markdown_export'`, `error == 'MISSING_REQUIRED_FIELDS'`, and `missing_fields == ['archive_base64']`.
- [ ] Run the focused test and confirm RED because export currently does not use `_require_fields`.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_markdown_export_archive_fields -q
```

### Task 2: Require export archive fields

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add `_require_fields(summary, 'markdown_export', export, ['archive_format', 'archive_encoding', 'archive_base64', 'files_are_inline', 'files'])` immediately after markdown export `_step_json` succeeds.
- [ ] Return the summary if validation fails.
- [ ] Keep existing final semantic checks for `zip`, `base64`, inline files, non-empty archive data, and `World.md` unchanged.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Verify and commit

**Files:**
- No `BETA_TESTING.md` update required because it already documents the archive response shape plus `MISSING_REQUIRED_FIELDS` diagnostics.

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
