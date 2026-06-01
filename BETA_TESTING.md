# WorldSim-Writer Beta Testing Playbook

Use this checklist to validate the local MVP before a beta handoff. The goal is to prove the main writing loop works, archived worlds stay read-only, and failures are reported with enough evidence to reproduce.

## 1. Prerequisites

- Work from the current feature branch; do not test uncommitted product-code experiments unless the test report says so.
- Backend commands run from `backend/` in the `worldsim` environment or the committed `.venv` used by this repo.
- Frontend commands run from `frontend/`.
- Copy `backend/.env.example` to `backend/.env` and replace the placeholder `SECRET_KEY` before starting the backend.
- For mock smoke, start the backend with `LLM_MOCK=true` so the chapter draft is deterministic and no real model call is made.
- For real-LLM smoke, set `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`, then run with `E2E_REAL_LLM=1`.

## 2. Build and test gates

Run these before inviting manual beta testers:

```bash
cd /opt/WorldSim-Writer/backend
PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
```

Expected: all backend tests pass.

```bash
cd /opt/WorldSim-Writer/frontend
npm run test
npm run build
```

Expected: all frontend tests pass and Vite reports `✓ built`.

## 3. Mock smoke

Start a local mock backend:

```bash
cd /opt/WorldSim-Writer/backend
LLM_MOCK=true .venv/bin/uvicorn app.main:app --reload
```

In another terminal, run the smoke script:

```bash
cd /opt/WorldSim-Writer/backend
BASE_URL=http://localhost:8000 PYTHONIOENCODING=utf-8 .venv/bin/python scripts/e2e_smoke.py
```

Pass criteria:

- The script exits 0.
- The printed JSON has `ok: true`.
- Checks include health, register/login, world creation, draft, approval preview/readiness/consistency, approve, events, and markdown export.
- `checks.health.status` is `ok`; if the smoke JSON stops at `failed_step: "health"` with `error: "HEALTH_STATUS_NOT_OK"`, inspect `/health`, backend startup logs, and dependency configuration before rerunning smoke.
- Auth evidence appears as either `checks.register` for a newly created smoke user or `checks.login` when `E2E_EMAIL` reuses an existing smoke account, such as after a previous run created the email before cleanup.
- `checks.health.migration_up_to_date` is `true`; if the smoke JSON stops at `failed_step: "health"` with `error: "MIGRATION_NOT_UP_TO_DATE"`, run `alembic upgrade head` from `backend/`, restart the backend, and rerun smoke.
- `checks.health.llm_mock` is `true`; if the smoke JSON stops at `failed_step: "health"` with `error: "BACKEND_LLM_MOCK_DISABLED"`, restart the backend with `LLM_MOCK=true` and rerun mock smoke.
- `checks.approval_preview.blocked` is `false`; if it is `true`, the smoke stops before formal approval with `failed_step: "approval_preview"` and `error: "APPROVAL_PREVIEW_BLOCKED"`, so regenerate the draft against the current world version and rerun smoke.
- `checks.approval_preview.proposed_change_count` is greater than `0`, proving at least one proposed character or foreshadow projection change is visible before approval; if it is `0`, the smoke stops before formal approval with `error: "NO_PROPOSED_PROJECTION_CHANGES"`.
- `checks.approval_readiness.blocked` is `false`; if it is `true`, the smoke stops before formal approval with `error: "APPROVAL_READINESS_BLOCKED"`, so review `checks.approval_readiness.blocking_reasons`, regenerate or repair the draft as instructed, and rerun smoke.
- `checks.approval_consistency.status` from `consistency_summary.status` is present, and `checks.approval_consistency.blocked` is `false`; if it is `true`, the smoke stops before formal approval with `error: "APPROVAL_CONSISTENCY_BLOCKED"`, so inspect `checks.approval_consistency.warnings` for severity/category/message/object details, adjust the proposed changes or regenerate the draft, and rerun smoke.
- `checks.approve.status` is `approved` and `checks.approve.approved_version` is present; if the smoke JSON stops at `failed_step: "approve"` with `error: "APPROVAL_STATUS_NOT_APPROVED"`, approval did not complete and later event/export checks are intentionally skipped.
- `checks.approve.world_version_incremented` is `true`, proving approval advanced the world version from the draft baseline; if the smoke JSON stops at `failed_step: "approve"` with `error: "WORLD_VERSION_NOT_INCREMENTED"`, inspect `checks.approve.approved_version` and `checks.approve.expected_world_version_after` before rerunning smoke.
- `checks.events.chapter_approved_seen` is `true`; if it is `false`, the smoke stops at `failed_step: "events"` with `error: "CHAPTER_APPROVED_EVENT_MISSING"`, so inspect event logging before trusting approval/export evidence.
- `checks.markdown_export.archive_format` is `zip`, `archive_encoding` is `base64`, inline archive content is present, and `files.World.md` appears in the inline preview; if not, the smoke stops at `failed_step: "markdown_export"` with `error: "MARKDOWN_EXPORT_INVALID_ARCHIVE"` and `invalid_fields` names the invalid archive evidence.

## 4. Real-LLM smoke

Use this only when a real OpenAI-compatible backend is configured:

```bash
cd /opt/WorldSim-Writer/backend
E2E_REAL_LLM=1 BASE_URL=http://localhost:8000 PYTHONIOENCODING=utf-8 .venv/bin/python scripts/e2e_smoke.py
# For slower providers or local model queues, increase the smoke client timeout:
E2E_REAL_LLM=1 E2E_TIMEOUT_SECONDS=180 BASE_URL=http://localhost:8000 PYTHONIOENCODING=utf-8 .venv/bin/python scripts/e2e_smoke.py
```

Pass criteria are the same as mock smoke except `checks.health.llm_mock` must be `false`, proving the backend is not in mock mode. If real-LLM draft generation times out before the backend responds, rerun with a larger `E2E_TIMEOUT_SECONDS` value such as `180`. If the smoke JSON stops at `failed_step: "health"` with `error: "BACKEND_LLM_MOCK_ENABLED"`, restart the backend with real `LLM_*` settings and `LLM_MOCK=false`, then rerun real-LLM smoke. If the real-LLM smoke fails but mock smoke passes, include the model settings except secrets and the full smoke JSON in the bug report. When the smoke JSON has `ok: false`, capture the diagnostic fields as well: `failed_step` identifies the failing API step, `status_code` records the HTTP status when available, and `response_body` contains a short redacted safe response snippet for triage; placeholders such as `[REDACTED_SECRET]` mean the smoke removed sensitive provider, credential, or request details before printing, including echoed `Authorization` bearer headers, JSON-shaped authorization fields, API keys, passwords, provider URLs, model names, and request messages. If `error` is `MISSING_REQUIRED_FIELDS`, `missing_fields` lists the fields absent from a successful API response; if `error` is `INVALID_FIELD_TYPES`, `invalid_fields` lists response fields that were present but unsafe for smoke checks to iterate, such as approval preview proposed-change collections, approval readiness reason/warning lists, approval consistency warning lists, approval consistency blocker counts, or event/export collections; if `error` is `INVALID_JSON_RESPONSE`, the API returned a successful HTTP status with malformed JSON and `response_body` contains the redacted body snippet; if `error` is `INVALID_JSON_RESPONSE_TYPE`, the API returned a successful HTTP status with valid but non-object JSON and `response_body` contains the redacted body snippet; `failed_step: "login"` means the fallback login response for an existing smoke email was malformed.

## 5. Manual main-flow QA

Use `http://localhost:5173` with the backend on `http://localhost:8000`.

1. Register or log in.
2. Create a world from the editable genre template or built-in sample flow.
3. Confirm the bookshelf lists the world and opening it shows world canon, characters, foreshadows, recent events, Story Arc Planner, Narrative Control Center, Global Search, Tags / Collections, Timeline Explorer, and World Archive.
4. Enter the studio.
5. Generate a chapter draft.
6. Review the draft, proposed changes, approval preview, readiness, and consistency information.
7. Approve the draft.
8. Return to the world overview.
9. Confirm `world_version` changes from `1` to `2`.
10. Confirm a `chapter_approved` event appears and at least one character or foreshadow projection changed when the model proposed changes.
11. Export Markdown and confirm a ZIP download link plus inline preview files appear.

## 6. Archive/read-only spot checks

After a successful main-flow run:

1. In World Archive, create a snapshot while the world is active.
2. Export Markdown ZIP.
3. Archive the world from the bookshelf/archive controls.
4. Reopen the archived world.
5. Confirm the UI says writing is paused and offers restore-writing controls.
6. Confirm write controls are hidden for chapter generation, story arc regeneration, world-bible managers, tag creation/assignment, and snapshot creation.
7. Confirm read tools still work: world overview, chapter history, timeline events, global search, tag browsing, snapshot list/compare, and markdown export.
8. Restore writing and confirm active-world controls return.

## 7. Cleanup

Smoke and manual beta data use `e2e-*` or tester-created accounts. To clean automated smoke accounts:

```bash
cd /opt/WorldSim-Writer/backend
PYTHONIOENCODING=utf-8 .venv/bin/python scripts/cleanup_e2e_data.py --confirm
```

The cleanup script should only delete users whose emails start with `e2e-` and their associated data. Do not manually delete `backend/worldsim-dev.db` unless the test owner explicitly asks for a full local reset.

## 8. Bug report evidence

Every beta bug report should include:

- Branch and commit SHA.
- Backend command and environment mode (`LLM_MOCK=true` or real LLM provider/model).
- Frontend URL and browser.
- Exact steps to reproduce.
- Expected vs actual result.
- Relevant terminal output, including smoke JSON or pytest/Vitest failure lines.
- Screenshot or short recording for UI issues.
- Whether cleanup was run.

## 9. Pass/fail summary template

```text
Commit:
Backend pytest: pass/fail + command output summary
Frontend tests: pass/fail + command output summary
Frontend build: pass/fail + command output summary
Mock smoke: pass/fail + smoke JSON ok/checks summary
Real-LLM smoke: pass/fail/skipped + reason
Manual main-flow QA: pass/fail + notes
Archive/read-only spot checks: pass/fail + notes
Cleanup: done/skipped + reason
Blocking issues:
Non-blocking issues:
```
