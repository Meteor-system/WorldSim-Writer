# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current repository state

This repository now contains the first runnable WorldSim-Writer MVP loop:

- FastAPI backend in [backend/](backend/) with SQLAlchemy models, Alembic migration, JWT auth, sample world APIs, OpenAI-compatible LLM client, chapter draft creation, approval, rejection, and world-state update tests.
- React/Vite/Tailwind frontend in [frontend/](frontend/) with login/register, sample-world creation, world overview, studio draft generation, and approval UI.
- Product and architecture source material remains [WorldSim-Writer.md](WorldSim-Writer.md).

## Commands

Run backend commands from [backend/](backend/) inside the project conda environment:

```bash
conda activate worldsim
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
pytest
pytest tests/test_narrative_approval.py -v
```

In this shell, `conda run` is often more reliable than `conda activate`:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd "D:/Code/Python/WorldSim-Writer/backend" && PYTHONIOENCODING=utf-8 pytest -v'
```

Run frontend commands from [frontend/](frontend/):

```bash
npm install
npm run dev
npm run build
npm run test
```

For local MVP acceptance, run the backend at `http://localhost:8000` and the frontend at `http://localhost:5173`.

## Source of truth

Use [WorldSim-Writer.md](WorldSim-Writer.md) as the authoritative product and architecture specification. It defines:

- MVP boundaries
- Product goals and target users
- Domain modules and state machines
- Recommended technical architecture
- API contract drafts
- Data model drafts
- Security, testing, and acceptance criteria
- Risk register and follow-up recommendations

## Product architecture overview

WorldSim-Writer is intended to be a long-form narrative operating system, not a one-shot text generator. Its core loop is:

1. Create or select a world and freeze its Truth Canon.
2. Manage characters, factions, map state, foreshadowing, and history.
3. Generate chapter drafts through a Showrunner -> Director -> Critics pipeline.
4. Let the user revise, approve, or reject the draft.
5. Only after user approval, commit the chapter and structured world-state events.
6. Continue simulation and generation from the updated world state.

The design principle is state-driven generation: world state, character state, event history, and the Truth Canon constrain chapter output.

## Implemented MVP backend structure

The backend is a FastAPI monolith with code-level domain separation:

- [backend/app/main.py](backend/app/main.py) creates the FastAPI app, CORS middleware, and health endpoint.
- [backend/app/core/](backend/app/core/) contains settings, database session wiring, password hashing, and JWT helpers.
- [backend/app/api/](backend/app/api/) contains shared dependencies and top-level router composition.
- [backend/app/auth/](backend/app/auth/) contains user model, schemas, service, and auth routes.
- [backend/app/world/](backend/app/world/) contains world model, built-in sample template, world service, overview schema, and world routes.
- [backend/app/character/](backend/app/character/) contains character and relation models and response schemas.
- [backend/app/foreshadow/](backend/app/foreshadow/) contains foreshadow model and response schema.
- [backend/app/event/](backend/app/event/) contains append-only event log model and response schema.
- [backend/app/llm/](backend/app/llm/) contains OpenAI-compatible Chat Completions client and structured response validation.
- [backend/app/narrative/](backend/app/narrative/) contains chapter and draft models, draft-generation service, approval transaction, and narrative routes.
- [backend/alembic/](backend/alembic/) contains the initial schema migration.
- [backend/tests/](backend/tests/) covers health/config, metadata registration, auth, sample world, LLM parsing/client behavior, and narrative approval.

## Implemented MVP frontend structure

The frontend is a Vite React app:

- [frontend/src/App.tsx](frontend/src/App.tsx) coordinates auth, world overview, and studio state.
- [frontend/src/api/](frontend/src/api/) contains the fetch wrapper and API response types.
- [frontend/src/auth/AuthPage.tsx](frontend/src/auth/AuthPage.tsx) handles login/register.
- [frontend/src/world/WorldPage.tsx](frontend/src/world/WorldPage.tsx) loads or creates the sample world and displays current projection state.
- [frontend/src/studio/StudioPage.tsx](frontend/src/studio/StudioPage.tsx) generates drafts, displays review context, and approves chapters.
- [frontend/tests/App.test.tsx](frontend/tests/App.test.tsx) covers the unauthenticated smoke path.

## State and consistency model

The current MVP implements these consistency rules:

- Chapter draft generation writes `Chapter` and `ChapterDraft`, but does not update formal world state.
- External model output is parsed and validated before being stored as proposed changes.
- Proposed character and foreshadow IDs must belong to the current world.
- Chapter approval checks `source_world_version` against `world.world_version` and returns `WORLD_VERSION_MISMATCH` on stale drafts.
- Chapter approval updates chapter approval fields, character goals/status, foreshadow status/description note, increments `world_version`, and writes a `CHAPTER_APPROVED` event in one database commit.
- Rejection changes only chapter review status and does not update world state.

## MVP scope

The MVP should continue to focus on the stable long-form writing loop. The implemented local loop covers auth, sample world creation, draft generation, approval, world-version updates, character updates, foreshadow updates, and event logging. Remaining MVP target areas include:

- Genre template creation and Truth Canon freeze beyond the built-in sample template
- Basic character and relationship management beyond read-only overview display
- Three-stage chapter generation: Showrunner, Director, Critics
- Foreshadow ledger beyond the current overview display
- Basic Obsidian export
- Single-app consistency around world state, event logs, and projections

The MVP explicitly should not include:

- 3D planet map or advanced map rendering
- Voice control
- Multi-user collaborative review
- Template marketplace or plugin ecosystem
- Complex branch-world management beyond basic snapshot design reservations
- Premature microservice, graph database, or vector database architecture

Only introduce Redis, Neo4j, standalone vector stores, service splits, or complex monitoring after a real bottleneck exists.

## Security and safety constraints

Current implemented safeguards:

- No anonymous formal writes.
- Store model keys, sync tokens, and database credentials outside business tables and outside the repo.
- Frontend must never receive high-privilege model API keys.
- External model output is validated before chapter approval can write state.

Target safeguards for the remaining MVP and later surfaces:

- Obsidian export must be limited to explicitly configured allowed directories and safe file types.
- Sync conflicts must never auto-overwrite either side.
- Audit login, permission changes, chapter approvals, manual corrections, rollback, delete, sync config changes, and exports.

## Testing and acceptance direction

Tests should cover the critical stateful writing loop rather than only isolated helpers:

- Unit tests for rule validation, state transitions, foreshadow updates, snapshots, and pure domain logic
- Integration tests for chapter generation -> review -> approval -> event log -> projection updates
- Regression/evaluation samples for prompt, memory retrieval, event rules, consistency, OOC risk, and foreshadow recovery
- Acceptance gates tied to the spec: consistency pass rate, foreshadow traceability, character-state traceability, chapter usability after light editing, and model cost visibility

## Working guidance for future Claude instances

- Read [WorldSim-Writer.md](WorldSim-Writer.md) before making product or architecture decisions.
- Keep recommendations scoped to the MVP unless the user explicitly asks about P1/P2 or final-state capabilities.
- Prefer tightening specs, schemas, contracts, state machines, and acceptance criteria before adding new feature ideas.
- Do not commit `.env`, secrets, credentials, `frontend/node_modules`, or `frontend/dist`.
- Do not push changes unless the user explicitly asks.
