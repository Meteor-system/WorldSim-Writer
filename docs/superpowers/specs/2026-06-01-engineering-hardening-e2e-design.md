# Engineering Hardening and E2E Reliability 1.0 Design

## Product-route analysis

The runnable MVP loop now depends on more than unit-level behavior: database migrations must be visible at startup, approval readiness must be machine- and human-readable, export semantics must be clear, and repeatable E2E validation must not depend on slow real LLM calls or leave test data behind. This work is engineering hardening before continuing MVP42. It does not add narrative product surface area; it makes the existing local MVP loop safer to run and verify.

The core product invariant remains unchanged: generated drafts can propose changes, but only user approval commits formal world-state changes and event history.

## Candidates and recommendation

### 1. Runtime health + E2E hardening bundle — recommended

Add migration status to `/health`, make Alembic's version table reproducibly able to store current long revision identifiers, add formal dev E2E smoke and optional real-LLM scripts with JSON summaries, add safe e2e-data cleanup, clarify event/export/readiness contracts, and document the commands.

Why this is best:

- It directly addresses the E2E failures and hidden operational risks already observed.
- It is small and testable: mostly backend helpers, scripts, docs, and response-compatible schema additions.
- It reduces future false positives from stale backend processes, real-LLM flakiness, and polluted dev databases.
- It preserves all existing API fields and frontend behavior.

### 2. Only add E2E scripts

Trade-off: helpful, but it would not expose migration drift or fix Alembic's version table length problem. The next backend restart could still fail late or misleadingly.

### 3. Full ops/admin subsystem

Trade-off: too large for this interruption. Admin APIs, dashboards, background health probes, and full fixture management can wait until the local MVP loop is stable.

## Recommendation

Implement **Engineering Hardening and E2E Reliability 1.0** before MVP42.

## Goals

1. `/health` remains backward-compatible with `status: "ok"` and also returns:
   - `migration.current`
   - `migration.head`
   - `migration.up_to_date`
   - `migration.status`
   - optional `migration.error` when migration status cannot be checked.
2. Alembic online migrations ensure `alembic_version.version_num` can store long revision identifiers by creating/widening the version table to `String(255)` before Alembic writes to it.
3. Add a formal backend E2E smoke script that:
   - defaults to quick mock-compatible validation,
   - supports `BASE_URL`,
   - outputs a standard JSON summary,
   - covers register -> create world -> draft -> approval preview/readiness/consistency -> approve -> events -> markdown export.
4. Add an optional real-LLM E2E mode with higher timeout and explicit documentation that the backend must be configured with real LLM settings.
5. Add a safe dev cleanup script/function that deletes only users whose email starts with `e2e-`, relying on existing cascades for associated worlds and data.
6. Standardize event type documentation and assertions on lower snake_case (`chapter_approved`), matching the actual API and database behavior.
7. Clarify `/worlds/{world_id}/export/markdown` semantics without breaking the current response by adding metadata fields and documenting that it returns both `archive_base64` and inline `files`.
8. Make approval-readiness responses more direct by adding compatible fields:
   - `ready: boolean`
   - `blocking_reasons: string[]`
   - `warnings: string[]`
   while preserving the existing `status`, `summary`, `world_version`, `checks`, and `high_risk_items` fields.

## Non-goals

- No frontend UI changes unless frontend build/type checks require them.
- No destructive cleanup outside `e2e-*` users.
- No new database tables beyond Alembic's existing version table maintenance.
- No change to chapter approval semantics, event log creation semantics, world version increments, or markdown file contents.
- No raw single-file markdown endpoint in this iteration.
- No dynamic workflows, no subagents, and no code-review subagent.

## Backend design

### Migration health

Create `app/core/migrations.py` with two responsibilities:

- `ensure_alembic_version_table_capacity(connection)` creates `alembic_version(version_num VARCHAR(255) PRIMARY KEY)` if missing and widens PostgreSQL/MySQL-style existing columns when supported.
- `get_migration_status(engine=database.engine)` uses Alembic `ScriptDirectory` and `MigrationContext` to compare current database heads with repository heads.

`/health` calls `get_migration_status()` and returns `status: "ok"` even when migration status cannot be checked. A DB or Alembic error is reported inside `migration.status == "unknown"`, not as a health endpoint 500.

### Alembic version table capacity

Update `backend/alembic/env.py` to call `ensure_alembic_version_table_capacity(connection)` before `context.configure(...)` and `context.run_migrations()` in online mode. This makes fresh local databases and existing databases reproducible without shortening current revision IDs.

### Approval readiness compatibility fields

`get_approval_readiness()` continues building existing checks. It derives:

- `ready = readiness_status == "ready"`
- `blocking_reasons = [check["message"] for check in checks if check["status"] == "fail"]`
- `warnings = [check["message"] for check in checks if check["status"] == "warning"]`

The schema adds these fields with no removal of existing fields.

### Markdown export semantics

Keep `POST /worlds/{world_id}/export/markdown`. Add explicit metadata:

- `archive_format: "zip"`
- `archive_encoding: "base64"`
- `files_are_inline: true`

Existing `archive_filename`, `archive_base64`, and `files` remain unchanged.

### E2E and cleanup scripts

Add:

- `backend/app/devtools/e2e_cleanup.py` — safe cleanup function for `e2e-*` users.
- `backend/scripts/cleanup_e2e_data.py` — CLI wrapper with `--dry-run` default and `--confirm` to delete.
- `backend/scripts/e2e_smoke.py` — HTTP API smoke script. It accepts `--mode smoke|real-llm`, `--cleanup-db`, `--timeout`, and `BASE_URL`. It always prints one JSON object with `ok`, `mode`, `base_url`, `steps`, and `cleanup`.

Smoke mode assumes the backend was started with `LLM_MOCK=true` for speed and determinism. Real-LLM mode is opt-in and uses a longer timeout.

## Documentation design

Update README and CLAUDE.md to:

- use `chapter_approved`, not `CHAPTER_APPROVED`, for actual API/event assertions,
- document `/health` migration fields,
- document `LLM_MOCK=true` smoke E2E setup and optional real-LLM mode,
- document safe E2E cleanup,
- document `/export/markdown` response shape (`archive_base64` zip plus inline `files`).

Update `WorldSim-Writer.md` examples/event enum to lower snake_case so the product source of truth no longer contradicts the implemented API.

## Testing strategy

Use strict TDD:

1. Add failing backend tests for health migration fields and Alembic version table capacity.
2. Add failing backend tests for approval-readiness `ready`, `blocking_reasons`, and `warnings` fields.
3. Add failing backend tests for markdown export semantic metadata.
4. Add failing backend tests for docs event casing.
5. Add failing backend tests for safe E2E cleanup and script JSON summary helpers.
6. Implement minimal code to pass each test.
7. Run targeted backend pytest covering health, migrations, readiness, export, E2E scripts, docs event casing, and existing event consistency tests.
8. Run necessary frontend targeted tests/build to ensure API type or doc changes did not break the frontend.
9. Run smoke E2E against a restarted backend configured with `LLM_MOCK=true`.

## Acceptance criteria

- `/health` includes migration current/head/up_to_date and reports `up_to_date=true` after backend restart against an upgraded DB.
- Alembic online migration setup creates or widens `alembic_version.version_num` to handle long revision IDs reproducibly.
- E2E smoke script passes with backend mock mode, prints JSON summary, and covers the full local MVP loop through markdown export.
- Optional real-LLM mode is documented and available.
- Cleanup deletes only `e2e-*` users and associated data; dry-run is the default.
- README, CLAUDE.md, WorldSim-Writer.md, tests, and scripts use `chapter_approved` for actual event assertions.
- Markdown export tests and docs clearly describe `archive_base64` zip plus inline `files`.
- Approval-readiness includes `ready`, `status`, `blocking_reasons`, and `warnings` while keeping older fields.
- Targeted backend pytest, necessary frontend tests/build, and smoke E2E pass before commit and after fast-forward merge to main.

## Risks and mitigations

- **Health endpoint could 500 when DB is down.** Catch migration-check errors and report `migration.status == "unknown"` while preserving `status: "ok"`.
- **Alembic table capacity fix could be dialect-specific.** Use SQLAlchemy table creation for missing tables and only run dialect-specific widen SQL for supported dialects; SQLite remains safe because it does not enforce varchar length.
- **E2E cleanup could delete real data.** Restrict deletion to `User.email LIKE 'e2e-%'`; dry-run is default and destructive deletion requires `--confirm`.
- **Real LLM mode could be slow.** Keep smoke mode default and document mock-mode startup clearly.
- **Response additions could break clients.** Only add optional/extra fields; do not remove or rename existing response fields.

## Self-review

- No placeholders remain.
- The scope is focused on engineering reliability before MVP42.
- Every user-requested target maps to a goal, backend/doc/script design item, and acceptance criterion.
- The design preserves the core approval/canon invariant and existing frontend behavior.

## Implementation status — 2026-06-01

Implemented on `feat/engineering-hardening-e2e`:

- `/health` now returns backward-compatible `status: "ok"` plus `migration.current`, `migration.head`, `migration.up_to_date`, and `migration.status`; migration-check failures report `migration.status: "unknown"` without making `/health` return 500.
- Alembic online migrations call a version-table capacity helper before running migrations; the helper creates `alembic_version.version_num` as `String(255)` and widens supported SQL dialects.
- Approval-readiness responses now include `ready`, `blocking_reasons`, and `warnings` while retaining existing fields.
- Markdown export responses now include `archive_format: "zip"`, `archive_encoding: "base64"`, and `files_are_inline: true` while keeping `archive_base64` and inline `files`.
- `scripts/e2e_smoke.py` runs the API smoke path using `BASE_URL`, default mock-compatible mode, optional `E2E_REAL_LLM=1`, and JSON summary output.
- `scripts/cleanup_e2e_data.py` dry-runs by default and requires `--confirm` to delete only `e2e-*` users plus associated worlds/snapshots/tags/chapters/events/projections.
- README, CLAUDE.md, and WorldSim-Writer.md no longer assert `CHAPTER_APPROVED`; actual event assertions use `chapter_approved`.

Verification evidence captured before commit:

- RED observed for missing migration helpers, health migration fields, readiness fields, markdown export metadata, E2E cleanup/scripts, event docs/env docs, and cleanup dry-run behavior.
- Targeted backend hardening tests: `34 passed, 2 warnings`.
- Frontend tests: `22 passed`, `145 passed`.
- Frontend build succeeded with `tsc && vite build`.
- Mock smoke E2E returned JSON summary with `"ok": true` and `health.migration_up_to_date: true`.
- Direct `/health` check returned `migration.current == migration.head == "0012_add_tags"` and `up_to_date: true`.
