# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status and source material

WorldSim-Writer currently contains a runnable local MVP loop: FastAPI backend, Vite/React frontend, SQLAlchemy/Alembic persistence, JWT auth, sample-world creation, OpenAI-compatible chapter drafting, draft approval/rejection, and world-state projection updates.

Use `WorldSim-Writer.md` as the product/architecture source of truth for product-scope decisions, but verify against the current code before treating a capability as implemented. That document still contains design-stage statements and future target capabilities that are no longer true for the repository state.

There are no Cursor rules (`.cursor/rules/`, `.cursorrules`) or Copilot instructions (`.github/copilot-instructions.md`) in this repo at the time this file was written.

## Commands

### Backend

Run backend commands from `backend/` in the `worldsim` conda environment.

```bash
conda activate worldsim
cp .env.example .env
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
```

`backend/.env.example` documents required settings. Change `SECRET_KEY` from the example value before starting the app; `Settings` rejects the placeholder. Set `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` before generating drafts.

Useful backend verification commands:

```bash
pytest
pytest tests/test_narrative_approval.py -v
pytest tests/test_narrative_approval.py::test_approve_chapter_updates_world_character_foreshadow_and_events -v
pytest --cov=app
```

In this shell, `conda run` can be more reliable than `conda activate`:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest -v'
```

### Frontend

Run frontend commands from `frontend/`.

```bash
npm install
npm run dev
npm run build
npm run test
npm run test -- src/path/to.test.tsx
```

The frontend dev server defaults to `http://localhost:5173`; the backend defaults used by the frontend client point at `http://localhost:8000` unless `VITE_API_BASE_URL` is set.

There are currently no repository lint scripts in the frontend package or backend pyproject. The frontend package has a Vitest command configured, but no committed `*.test.*` or `*.spec.*` files were present when this file was updated.

### Manual MVP check

Run the backend at `http://localhost:8000` and frontend at `http://localhost:5173`, then verify the local loop from the README:

1. Register or log in.
2. Create the built-in sample world.
3. Enter the studio.
4. Generate a chapter draft.
5. Approve the draft.
6. Confirm `world_version` increments, a `CHAPTER_APPROVED` event appears, and at least one proposed projection change is visible.

## Backend architecture

The backend is a FastAPI monolith with domain folders rather than separate services. `app.main:create_app()` configures CORS from settings and includes `app.api.router`, which mounts auth, world, and narrative routers. `/health` is defined directly in `app.main`.

Configuration and persistence are centralized in `app.core`:

- `config.py` loads Pydantic settings from `.env` and rejects the placeholder local secret.
- `database.py` defines SQLAlchemy `Base`, engine/session factory, request-scoped `get_db()`, and `import_models()` for metadata registration.
- `security.py` handles password hashing and JWT helpers.

Auth lives in `app.auth`: registration/login create JWTs, `app.api.dependencies.require_user` resolves the current user, and protected routes reject anonymous formal writes.

World state is split between current projection tables and append-only history:

- `app.world.service.create_sample_world()` seeds the built-in template into `World`, `Character`, `CharacterRelation`, and `Foreshadow` rows.
- `get_world_overview()` aggregates the current projection plus recent `EventLog` entries for the frontend overview.
- `require_owned_world()` is the common ownership boundary for world-scoped operations.

Narrative generation and approval are intentionally transactional:

- `create_chapter_draft()` reads the current world projection, builds model messages, calls the OpenAI-compatible `LLMClient`, validates structured model output, and stores `Chapter`/`ChapterDraft` records without changing formal world state.
- `approve_chapter()` locks the world row, checks the draft `source_world_version`, applies proposed character/foreshadow projection changes, increments `world_version`, and writes a `CHAPTER_APPROVED` event in one commit.
- Rejecting a chapter only marks the chapter rejected and must not update world projection state.

The LLM boundary is in `app.llm`: the client speaks Chat Completions-style HTTP and parses responses into Pydantic schemas before narrative services persist proposed changes. Model-proposed character and foreshadow IDs must belong to the current world.

Alembic migrations live under `backend/alembic/`. Tests in `backend/tests/` use FastAPI `TestClient`, dependency overrides, and in-memory SQLite with JSONB compilation shims, so integration tests do not need a running Postgres instance.

## Frontend architecture

The frontend is a Vite React app with a small stateful flow rather than a router:

- `src/App.tsx` switches between auth, world overview, and studio modes based on local component state and the presence of `worldsim_token` in `localStorage`.
- `src/api/client.ts` is the central fetch wrapper. It adds JSON headers, attaches the bearer token, uses `VITE_API_BASE_URL` or `http://localhost:8000`, and throws response text on non-2xx responses.
- `src/api/types.ts` mirrors backend response shapes used by the UI.
- `src/auth/AuthPage.tsx` handles login/register.
- `src/world/WorldPage.tsx` lists/creates the sample world and renders the current projection.
- `src/studio/StudioPage.tsx` drafts chapters, displays review context/proposed changes, and approves chapters.

## Product and implementation boundaries

Keep work scoped to the stable MVP loop unless the user explicitly asks for P1/P2 or final-state capabilities. Current implemented scope centers on auth, built-in sample world creation, draft generation, approval/rejection, projection updates, event logging, and frontend review UI.

Remaining MVP targets from the product spec include genre template creation beyond the built-in sample, basic character/relationship management, a fuller Showrunner/Director/Critics pipeline, richer foreshadow ledger, basic Obsidian export, and consistency around world state/event logs/projections.

Explicit non-goals for the MVP include 3D planet maps, voice control, multi-user collaborative review, template marketplace/plugin ecosystem, complex branch-world management, premature microservices, graph databases, standalone vector stores, Redis, or complex monitoring before a real bottleneck exists.

When changing the stateful writing loop, preserve the core invariant from the spec: generated drafts can propose changes, but only user approval commits formal world-state changes and event history.
