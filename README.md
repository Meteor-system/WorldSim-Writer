# WorldSim-Writer

WorldSim-Writer is a long-form narrative creation system. The current MVP runs a local loop: register or log in, create a world from an editable genre template, generate a chapter draft through an OpenAI-compatible Chat Completions API, approve the draft, and see world state updates.

## Local setup

Backend:

```bash
conda activate worldsim
cd backend
cp .env.example .env
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Set `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` in `backend/.env` before generating a chapter draft. For fast local smoke E2E, start the backend with `LLM_MOCK=true` so chapter generation is deterministic and does not call a real model.

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
