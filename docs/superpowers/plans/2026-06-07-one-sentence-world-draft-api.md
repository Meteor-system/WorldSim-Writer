# One-Sentence World Draft API Implementation Plan

> **For agentic workers:** Inline TDD only. This run explicitly forbids dynamic workflows, subagents, and code-review subagents.

**Goal:** Add a backend endpoint that expands a one-sentence story brief into a validated `WorldCreateRequest` draft without creating a world or mutating canon/state/history.

**Architecture:** Add request/response schemas in `app.world.schemas`, a pure expansion service in `app.world.service`, and a `POST /worlds/brief/expand` route in `app.world.router`. The service calls `LLMClient.expand_world_brief()`, validates the model result through Pydantic plus starter-asset checks, and rejects unsafe protected-work terms.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy test fixtures, pytest, existing OpenAI-compatible `LLMClient` boundary.

---

## File Structure

- Test: `backend/tests/test_world_brief_expand.py`
  - RED tests for successful draft generation, no persistence, auth, blank/short brief validation, malformed model output, and protected-term rejection.
- Modify: `backend/app/world/schemas.py`
  - Add `WorldBriefExpandRequest`, `WorldBriefExpansion`, and `WorldBriefExpandResponse`.
- Modify: `backend/app/world/service.py`
  - Add prompt builder, model error mapping, model output validation, starter asset validation for drafts, protected-term guard, and `expand_world_brief()`.
- Modify: `backend/app/world/router.py`
  - Add `POST /worlds/brief/expand` route.
- Modify: `backend/app/llm/client.py`
  - Add mock and real `expand_world_brief()` method returning parsed JSON for service validation.

---

## TDD Steps

1. RED: write `backend/tests/test_world_brief_expand.py`.
2. RED command:
   `cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_world_brief_expand.py -v`
   Expected: fail because endpoint does not exist.
3. GREEN: implement schemas/service/router/LLM client method minimally.
4. GREEN command:
   `cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_world_brief_expand.py -v`
   Expected: pass.
5. Regression:
   - `cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_world_brief_expand.py tests/test_world_template.py tests/test_world_routes.py tests/test_import_node.py -v`
   - `git -C /opt/WorldSim-Writer diff --check`
6. Inline self-review for no persistence, no canon/EventLog mutation, no frontend implementation, no push/merge.
7. Commit: `feat: add one-sentence world draft endpoint`.
