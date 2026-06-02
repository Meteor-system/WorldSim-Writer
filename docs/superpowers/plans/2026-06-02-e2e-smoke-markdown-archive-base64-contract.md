# E2E Smoke Markdown Archive Base64 Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject non-string or empty markdown export `archive_base64` values before smoke reports a valid archive.

**Architecture:** Reuse the smoke script's top-level string-field validator for `archive_base64` after required export fields are present and before final archive validity checks. Document the diagnostic so beta testers can distinguish malformed archive body types from archive format/value failures.

**Tech Stack:** Python, httpx, pytest, Markdown.

---

## File map

- Modify `backend/tests/test_e2e_scripts.py` — add RED regression for non-string `archive_base64`.
- Modify `backend/scripts/e2e_smoke.py` — require `archive_base64` to be a non-empty string.
- Modify `BETA_TESTING.md` — document the `archive_base64` type diagnostic.
- Modify `backend/tests/test_event_docs.py` — require beta docs wording.
- Create `docs/superpowers/specs/2026-06-02-e2e-smoke-markdown-archive-base64-contract-design.md` — design record.
- Create `docs/superpowers/plans/2026-06-02-e2e-smoke-markdown-archive-base64-contract.md` — this implementation plan.

### Task 1: Add failing archive-base64 regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where markdown export returns all required archive fields but `archive_base64` is `['UEs=']`.
- [ ] Assert the smoke stops at `markdown_export` with `INVALID_FIELD_TYPES` and `invalid_fields == ['archive_base64']`.
- [ ] Assert all requests up to markdown export were made and no later step exists.
- [ ] Run the focused test and verify RED because the current smoke accepts truthy non-string archive bodies.

### Task 2: Implement archive-base64 string validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After required markdown export fields are present, call `_require_string_fields(summary, 'markdown_export', export, ['archive_base64'])`.
- [ ] Keep the existing missing-field diagnostic for absent `archive_base64`.
- [ ] Keep existing archive value checks for `archive_format`, `archive_encoding`, `files_are_inline`, and `files.World.md`.
- [ ] Run the focused test and verify GREEN.

### Task 3: Document markdown archive-body diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Update markdown export pass criteria to say `archive_base64` is a non-empty string.
- [ ] Update real-LLM diagnostics for `INVALID_FIELD_TYPES` to mention markdown archive body strings.
- [ ] Add docs coverage terms for `archive_base64` and markdown archive body strings.
- [ ] Run docs coverage tests.

### Task 4: Verify and commit

**Files:**
- Smoke script, smoke tests, beta docs, docs coverage test, and this task's spec/plan docs only.

- [ ] Run focused archive-base64 test.
- [ ] Run smoke-script tests.
- [ ] Run docs coverage.
- [ ] Run full backend tests.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve unrelated untracked files.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current branch without pushing or merging.
