# WorldSim-Writer

WorldSim-Writer is a long-form narrative creation system. The current MVP runs a local loop: register or log in, create the built-in sample world, generate a chapter draft through an OpenAI-compatible Chat Completions API, approve the draft, and see world state updates.

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

Set `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` in `backend/.env` before generating a chapter draft.

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

Manual MVP check:

1. Open the frontend at `http://localhost:5173`.
2. Register or log in.
3. Create the built-in sample world.
4. Enter the studio.
5. Generate a chapter draft.
6. Approve the draft.
7. Confirm `world_version` changes from `1` to `2`.
8. Confirm a `CHAPTER_APPROVED` event appears.
9. Confirm at least one character goal changes.
10. Confirm the foreshadow status changes when the model proposed a foreshadow update.

## Project structure

- `backend/` — FastAPI backend, SQLAlchemy models, Alembic migration, LLM client, and pytest suite.
- `frontend/` — Vite React frontend for auth, world overview, and studio approval flow.
- `WorldSim-Writer.md` — product and architecture source of truth.
- `docs/superpowers/` — design and implementation planning artifacts.
