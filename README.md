# WorldSim-Writer

**Current release: `0.2.0-beta.1` restricted Beta — July 30, 2026**

WorldSim-Writer is a long-form narrative creation and world-state governance system. Authors can create a story world from a seed, editable template, imported reference material, or a one-sentence brief; generate and revise chapter drafts in Studio; inspect proposed world changes and consistency risks; and explicitly write an approved chapter into canon.

> **Core invariant:** generated drafts, plans, candidate assets, and style handbooks may propose or influence content, but only explicit user approval commits chapter content and approved projection changes to canonical world state and event history.

## Beta scope

This repository is ready for a **restricted local or private-network Beta** with trusted testers, controlled accounts, an operator monitoring the service, and either deterministic `LLM_MOCK=true` or a separate low-budget LLM credential.

It is **not yet a turnkey public SaaS release**. The committed Compose stack serves PostgreSQL and the backend API only; frontend static hosting, TLS/reverse-proxy configuration, public abuse/rate limiting, invite-only account provisioning, and browser-session hardening remain deployment responsibilities before an Internet-facing rollout. The API stays bound to loopback by default.

## Delivered Beta capabilities

- **Fast story start:** built-in world seeds, editable genre presets, manual creation, and one-sentence world-draft generation. Generated creation drafts remain editable and do not create a world until confirmed.
- **Reference workflow:** Import Node candidate material and abstract style-handbook previews can guide original world and chapter generation without becoming canon automatically.
- **Chapter Studio:** outline and draft generation, manual edits, stash snapshots, draft-version history and diff, whole-draft revision, paragraph rewrite/polish, literary critique, character-arc analysis, reject, abandon, and resume-active-session flows.
- **Opening quality gate:** the first chapter records unique, directly located evidence for background, protagonist identity, motivation, personality evidence, conflict goal, and locked limited-third-person POV. Locked-POV evidence must include the locked character and a subjective perception, judgment, emotion, intent, or knowledge-boundary cue; stale or failing evidence blocks canon approval.
- **Canon governance:** approval preview, readiness, consistency checks, explicit locked-POV confirmation for the opening chapter, transactional approval, world-version advancement, and append-only event evidence.
- **Story operations:** world dashboard, story arc and serial plans, next-chapter preparation, narrative health, open threads, world pulse, chapter history, timeline, search, tags/collections, character/relationship/foreshadow management, snapshots, archive/restore, comparison, and Markdown ZIP export.
- **LLM modes:** deterministic dynamic mock plus configurable OpenAI-compatible `responses` and `chat_completions` provider modes. Real-provider canaries are opt-in and cost-acknowledged.

## Architecture

- `backend/` — FastAPI, SQLAlchemy, Alembic, PostgreSQL/SQLite-compatible tests, authentication, narrative services, LLM adapters, operational scripts, and pytest coverage.
- `frontend/` — React, TypeScript, Vite, Tailwind, Vitest, and Testing Library.
- `compose.yaml` — PostgreSQL, one serialized migration job, and the hardened backend API container. It does not serve the frontend.
- `backend/uv.lock` and `frontend/package-lock.json` — locked local/test dependency resolutions for the current Beta candidate; rebuild and verify the backend container for each release.

## Quick start

### 1. Backend

Use Python 3.12 or newer. From `backend/`:

```bash
cp .env.example .env
# Replace SECRET_KEY and configure DATABASE_URL.
# Keep LLM_MOCK=true for deterministic local evaluation without provider cost.
uv sync --frozen --extra dev
uv run python scripts/run_migrations.py
uv run uvicorn app.main:app --reload
```

If `uv` is unavailable, install with `python -m pip install -e ".[dev]"` and run the same Python/Uvicorn commands directly. The reload command is development-only; deployed APIs must use `scripts/run_api.py` as described below.

### 2. Frontend

From `frontend/`:

```bash
npm ci
npm run dev
```

The frontend opens at `http://localhost:5173` and defaults to `http://localhost:8000` for the API. Set `VITE_API_BASE_URL` at build or development time when the API uses another origin:

```bash
VITE_API_BASE_URL=https://api.example.test npm run build
```

The backend `FRONTEND_ORIGIN` must match the browser origin. For local development only, `localhost` and `127.0.0.1` are accepted as loopback aliases when the scheme and port match. The current release does not include a frontend container or public static-hosting configuration.

## Configuration

Copy `backend/.env.example` for direct backend development or the root `.env.example` for Compose. Never commit either real `.env` file.

Important LLM settings:

| Variable | Purpose |
| --- | --- |
| `LLM_MOCK` | `true` uses deterministic, prompt-shaped local responses and makes no provider request. |
| `LLM_BASE_URL` | Base URL for the configured OpenAI-compatible provider. |
| `LLM_API_KEY` | Provider credential; use a separate low-budget Beta key. |
| `LLM_MODEL` | Provider model identifier. |
| `LLM_API_MODE` | `responses` or `chat_completions`; defaults to `responses`. |
| `LLM_TIMEOUT_SECONDS` | Connect/write/pool timeout, bounded to 1–300 seconds. |
| `LLM_READ_TIMEOUT_SECONDS` | Model read timeout, bounded to 1–1800 seconds; defaults to 300. |

For an Internet-facing deployment, do not use a plaintext remote `LLM_BASE_URL`, unrestricted public registration, or an unbudgeted provider credential.

## Canon and approval model

1. World creation drafts, imports, style handbooks, story arcs, serial plans, outlines, and chapter drafts are proposals.
2. The latest chapter draft is reviewed in Studio with approval preview, readiness, consistency, quality, critic, and character-arc evidence.
3. Manual edits and AI revisions create new draft versions; they do not advance the world version.
4. The opening chapter must have a current passing quality report and an explicit confirmation of the locked POV.
5. Only the approval transaction writes approved content and selected projection changes, increments the world version, and appends event history.
6. Archived worlds reject mutations while preserving reading, history, search, snapshot comparison, export, and later restoration.

## Verification

Run the project-configured backend suite from the repository root:

```bash
python -m pytest -q -c backend/pyproject.toml backend/tests
```

Run frontend tests and the production build:

```bash
npm --prefix frontend run test
npm --prefix frontend run build
```

Validate dependency locks and the Compose contract:

```bash
uv lock --check --project backend
uv sync --frozen --extra dev --project backend --dry-run
# After setting safe non-placeholder POSTGRES_PASSWORD and SECRET_KEY:
docker compose config --quiet
```

### Mock API smoke

Start a backend configured with `LLM_MOCK=true`, then run:

```bash
BASE_URL=http://localhost:8000 PYTHONIOENCODING=utf-8 \
python backend/scripts/e2e_smoke.py
```

The smoke covers health and migration state, register/login, world creation, chapter draft, opening-quality and approval checks, explicit approval, world-version advancement, events, and Markdown ZIP export. It prints one JSON result and exits nonzero on the first failed release gate.

Clean automated `e2e-*` accounts only against the intended test database:

```bash
PYTHONIOENCODING=utf-8 python backend/scripts/cleanup_e2e_data.py --confirm
```

### Optional real-provider canaries

Real-provider tests are skipped by default and ordinary tests block accidental external LLM calls. Running them incurs provider cost and requires all opt-ins plus real non-placeholder provider settings:

```bash
RUN_REAL_LLM_CANARY=1 LLM_CANARY_ACK_COST=1 \
python -m pytest -q -c backend/pyproject.toml --run-real-llm \
-m real_llm backend/tests/test_real_llm_canary.py
```

The canaries exercise a world-creation draft and an in-memory outline-to-chapter flow without creating database records. They are not a substitute for long-context, multi-chapter, rate-limit, recovery, cost, and literary-quality evaluation.

See `BETA_TESTING.md` for the full manual handoff, archive/read-only, failure, and bug-report checklist.

## Release migrations and API runtime

Run a release from `backend/` in this order:

```bash
python scripts/run_migrations.py
python scripts/run_api.py
```

`run_migrations.py` is a dedicated serialized pre-deploy job. It runs `alembic upgrade head`, verifies repository and database heads independently, returns stable failure codes, and does not print database credentials or raw migration exceptions. Do not run migrations from FastAPI startup or from every API worker.

`run_api.py` starts API workers only. Keep `/ready` as the traffic gate and `/live` as the process liveness probe. Defaults are `127.0.0.1:8000`, one worker, concurrency limit `100`, backlog `2048`, keep-alive `5` seconds, and graceful shutdown timeout `30` seconds. Configuration comes from the documented `API_*` variables. Stop with `SIGTERM` on POSIX or `CTRL_BREAK_EVENT` from a Windows process group, then allow the configured graceful-shutdown window before escalating.

Proxy headers default to `API_PROXY_HEADERS=false` and `API_FORWARDED_ALLOW_IPS=127.0.0.1`. Enable proxy headers only when every direct connection comes from a known reverse proxy, and set `API_FORWARDED_ALLOW_IPS` to exact IP addresses or CIDR networks. Never use wildcard proxy trust such as `*`, `0.0.0.0/0`, or `::/0`.

The application emits structured request logs without request bodies, query strings, authorization headers, or LLM prompts. Uvicorn access logs and its `Server`/`Date` response headers are disabled by the production runner.

## Docker backend release stack

From the repository root:

```bash
cp .env.example .env
# Replace POSTGRES_PASSWORD and SECRET_KEY.
# Replace LLM settings too when LLM_MOCK=false.
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps --all
docker compose logs migrate
```

The stack waits for PostgreSQL, runs the migration container once, and starts the API only after migration success. The API becomes healthy through `/ready`; `/live` and `/ready` should return `200`. The image runs as UID/GID `10001`; API and migration containers use read-only root filesystems, dropped Linux capabilities, `no-new-privileges`, and bounded process counts. PostgreSQL is not published to the host.

The API is exposed only on `127.0.0.1:8000` by default. Keep that boundary for a restricted Beta. Do not bind `COMPOSE_API_BIND_ADDRESS=0.0.0.0` without a reviewed firewall, TLS reverse proxy, host/origin policy, authentication hardening, rate and body-size limits, LLM quotas, and operational monitoring.

`docker compose down` preserves the PostgreSQL volume. Never use `docker compose down --volumes` for retained Beta data.

## PostgreSQL backup and restore drill

Install PostgreSQL client tools compatible with the server major version. Store dumps outside the repository in encrypted, access-controlled storage:

```bash
python backend/scripts/postgres_backup.py backup \
  --output /secure/backups/worldsim-YYYYmmddTHHMMSSZ.dump
```

Verify against a separately provisioned, pristine database whose name clearly marks it as a test target:

```bash
RESTORE_DATABASE_URL=postgresql+psycopg://.../worldsim_restore_test \
python backend/scripts/postgres_backup.py verify-restore \
  --backup-file /secure/backups/worldsim-YYYYmmddTHHMMSSZ.dump
```

The scripts never overwrite an existing backup, create/drop/clean a restore database, or print database URLs and raw client errors. Restore succeeds only when the target was empty and its Alembic heads match the repository. Migration `0014_add_chapter_draft_quality_report` adds approval evidence; production rollback should use a verified backup and forward fix rather than a routine downgrade that drops this column.

## Restricted Beta operating constraints

- Use trusted testers, controlled account distribution, loopback/VPN/private-network access, and operator supervision.
- Prefer `LLM_MOCK=true` for functional QA. If using a real provider, isolate the credential, enforce a low budget, and monitor usage manually.
- Do not advertise the repository as a hardened public SaaS stack: application-level rate limiting, invitation-only registration, session revocation/Cookie migration, CSP/security headers, request-size/token budgets, frontend hosting, TLS, and public monitoring are not delivered here.
- The browser currently stores the bearer token in `localStorage`; avoid untrusted scripts/extensions and do not use production-value accounts in the restricted Beta.
- Back up retained PostgreSQL data before every release and verify restore on an isolated database.
- Record the exact commit SHA and execute `BETA_TESTING.md` before handing the build to testers.

## Export and archive behavior

`POST /worlds/{world_id}/export/markdown` returns JSON containing a base64-encoded ZIP plus inline preview files. Archiving a world is reversible and does not delete chapters, snapshots, exports, or event history. Create a snapshot and export before pausing a long-running novel.

## Project structure and documentation

- `backend/app/` — API and domain packages: auth, world, narrative, LLM, characters, relations, foreshadows, imports, tags, snapshots, exports, and narrative control center.
- `backend/alembic/` — versioned PostgreSQL schema migrations.
- `backend/scripts/` — release migrations, production API runner, backup/restore drill, E2E smoke, and cleanup tools.
- `backend/tests/` — pytest suite, including opt-in PostgreSQL/concurrency and real-LLM markers.
- `frontend/src/` — React application, API client, world operations, and Studio.
- `frontend/tests/` — application-level frontend regression tests.
- `compose.yaml` and `.env.example` — restricted Beta backend stack and runtime template.
- `WorldSim-Writer.md` — product vision and architecture reference; future-looking sections are not release claims.
- `docs/UX_UPDATE_PHASE.md` — delivered Beta UX scope and regression contract.
- `BETA_TESTING.md` — manual release and tester handoff playbook.
