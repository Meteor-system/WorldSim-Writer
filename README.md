# WorldSim-Writer

WorldSim-Writer is a long-form narrative creation system. The current MVP runs a local loop: register or log in, create a world from an editable genre template, generate a chapter draft through an OpenAI-compatible Chat Completions API, approve the draft, and see world state updates.

## Local setup

Backend development:

```bash
conda activate worldsim
cd backend
cp .env.example .env
pip install -e '.[dev]'
python scripts/run_migrations.py
uvicorn app.main:app --reload
```

The direct Uvicorn command above is for local development only. Use the production runtime entry point below for a deployed API.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Set `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` in `backend/.env` before generating a chapter draft. For fast local smoke E2E, start the backend with `LLM_MOCK=true` so chapter generation is deterministic and does not call a real model.

## Release migrations

Run `python scripts/run_migrations.py` once as a dedicated, serialized pre-deploy job before starting or rolling API workers. The job runs `alembic upgrade head`, then independently verifies that the database heads match the repository heads. It exits nonzero with a stable error code when upgrade or verification fails and does not print the database URL or underlying exception details.

Do not run migrations from FastAPI startup or from every API worker. The release platform must allow only one migration job at a time; API readiness remains the traffic gate until the schema is current.

## Production API runtime

Start a release in this order from `backend/`:

```bash
python scripts/run_migrations.py
python scripts/run_api.py
```

`run_migrations.py` is the serialized pre-deploy job. `run_api.py` starts only API workers and never upgrades the database. Keep `/ready` as the traffic gate and `/live` as the process liveness probe. On POSIX platforms Uvicorn replaces the launcher process, and on Windows it runs in the launcher process, so the API process directly owns worker supervision and graceful shutdown. Send `SIGTERM` on POSIX or `CTRL_BREAK_EVENT` from a Windows process group and allow the configured shutdown timeout before escalating.

The runtime defaults to `127.0.0.1:8000`, one worker, a per-worker concurrency limit of `100`, backlog `2048`, keep-alive `5` seconds, and graceful shutdown timeout `30` seconds. Configure these with `API_HOST`, `API_PORT`, `API_WORKERS`, `API_LIMIT_CONCURRENCY`, `API_BACKLOG`, `API_TIMEOUT_KEEP_ALIVE_SECONDS`, and `API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS`. The launcher validates bounded values and ignores `UVICORN_*`, `WEB_CONCURRENCY`, and `FORWARDED_ALLOW_IPS` override variables so deployment behavior comes only from the documented `API_*` interface.

Proxy headers are disabled by default with `API_PROXY_HEADERS=false`. Enable them only when every direct connection reaches the API through known reverse proxies, then set `API_FORWARDED_ALLOW_IPS` to their exact IP addresses or CIDR networks. Hostnames, URLs, Unix socket literals, empty entries, unspecified addresses, malformed networks, and wildcard trust such as `*`, `0.0.0.0/0`, or `::/0` are rejected. Never use wildcard proxy trust.

Uvicorn access logs are disabled because the application already emits structured request logs without query strings, credentials, or request bodies. Uvicorn `Server` and `Date` response headers are also disabled; a reverse proxy may add its own headers outside this process.

## Docker backend release stack

The committed Compose stack packages the current backend release boundary: PostgreSQL, one serialized migration job, and the production API runner. It intentionally does not serve the frontend yet; keep using the frontend development workflow above until a separate static-hosting and reverse-proxy batch is delivered.

From the repository root, copy the Compose environment template and replace every placeholder. The root `.env` is ignored by Git and excluded from the backend image build context, but Docker receives its values at runtime, so restrict access to that file and never commit it.

```bash
cp .env.example .env
# Replace POSTGRES_PASSWORD, SECRET_KEY, and real LLM settings when LLM_MOCK=false.
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps --all
docker compose logs migrate
```

`docker compose up -d` waits for PostgreSQL health, runs `python scripts/run_migrations.py` once, and starts the API only after that job exits successfully. A successful release shows `migrate` exited with code `0`, `api` becomes healthy through `/ready`, and `GET http://127.0.0.1:8000/live` plus `/ready` return `200`. The image runs as UID/GID `10001`, the migration and API containers use read-only root filesystems with dropped Linux capabilities, and PostgreSQL is not published to the host.

The API is published only on `127.0.0.1:8000` by default. Keep that loopback boundary when a host reverse proxy terminates TLS. Do not set `COMPOSE_API_BIND_ADDRESS=0.0.0.0` without an explicit firewall, TLS termination, authentication review, and the proxy trust configuration described above. `docker compose down` stops the stack while preserving the named PostgreSQL volume; never run `docker compose down --volumes` for retained Beta data.

## PostgreSQL backups and restore drills

Install PostgreSQL client tools compatible with the server major version, then create a custom-format backup in a protected directory outside the repository:

```bash
cd backend
python scripts/postgres_backup.py backup --output /secure/backups/worldsim-YYYYmmddTHHMMSSZ.dump
```

The backup command reads only `DATABASE_URL`, refuses to overwrite an existing path, writes through a same-directory temporary file, and reports the final size and SHA-256 digest. Database URLs, passwords, client stderr, and tracebacks are not printed. Store the resulting dump encrypted with restricted access and apply an external retention policy; the script does not upload, rotate, or delete backups.

Periodically verify a backup against a separately provisioned PostgreSQL database whose name is clearly isolated, such as `worldsim_restore_test`:

```bash
cd backend
RESTORE_DATABASE_URL=postgresql+psycopg://.../worldsim_restore_test \
python scripts/postgres_backup.py verify-restore --backup-file /secure/backups/worldsim-YYYYmmddTHHMMSSZ.dump
```

`verify-restore` never creates, drops, cleans, or reuses database objects. The target must already exist, differ from the source database, use a `test_*`, `*_test`, or `*_test_*` name, and contain no user objects. Restore runs in one transaction and succeeds only when the restored Alembic heads match the repository heads. Recreate the isolated target before every drill; never set `RESTORE_DATABASE_URL` to production.

## Verification

Run backend tests:

```bash
conda activate worldsim
cd backend
pytest
```

Run frontend tests and build:

```bash
cd frontend
npm run test
npm run build
```

Run fast API smoke E2E against a running backend in mock mode:

```bash
cd backend
LLM_MOCK=true uvicorn app.main:app --reload
BASE_URL=http://localhost:8000 PYTHONIOENCODING=utf-8 python scripts/e2e_smoke.py
```

For optional real-LLM smoke, start the backend with real `LLM_*` settings and run `E2E_REAL_LLM=1 BASE_URL=http://localhost:8000 python scripts/e2e_smoke.py`. Both modes print a JSON summary and cover register → create world → draft → approval preview/readiness/consistency → approve → events → markdown export. Clean generated `e2e-*` data with:

```bash
cd backend
PYTHONIOENCODING=utf-8 python scripts/cleanup_e2e_data.py --confirm
```

`POST /worlds/{world_id}/export/markdown` returns a JSON payload with `archive_format: "zip"`, `archive_encoding: "base64"`, `archive_base64`, `files_are_inline: true`, and inline `files` entries for preview or direct use.

## Pausing one novel and switching to another

Recommended flow when you are not ready to continue the current novel:

1. Open the current novel from the bookshelf.
2. In `World Archive`, click `创建世界快照` to freeze the current world version.
3. Click `导出世界档案` and download the Markdown ZIP for an offline copy.
4. Return to `作品书架`.
5. Archive the paused novel. Archiving is a reversible status marker; it never deletes the world, chapters, snapshots, or exports.
6. Create a new novel or open another active novel and continue writing.

Manual MVP check:

1. Open the frontend at `http://localhost:5173`.
2. Register or log in.
3. Create a world from an editable genre template.
4. Enter the studio.
5. Generate a chapter draft.
6. Approve the draft.
7. Confirm `world_version` changes from `1` to `2`.
8. Confirm a `chapter_approved` event appears.
9. Confirm at least one character goal changes.
10. Confirm the foreshadow status changes when the model proposed a foreshadow update.

## Project structure

- `backend/` — FastAPI backend, SQLAlchemy models, Alembic migration, LLM client, and pytest suite.
- `frontend/` — Vite React frontend for auth, world overview, and studio approval flow.
- `WorldSim-Writer.md` — product and architecture source of truth.
- `docs/superpowers/` — design and implementation planning artifacts.
