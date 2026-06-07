# E2E Brief Auto-Draft Migration Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. This session must execute inline because the user explicitly forbids dynamic workflows, subagents, agents, and code-review subagents. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the real one-sentence open-book E2E loop so brief expansion tolerates common real-LLM formatting, Studio auto-first-draft cannot remain indefinitely pending, and Alembic upgrades from 0012 to 0013 create import tables.

**Architecture:** Keep changes minimal and localized. Backend parsing belongs at the LLM boundary plus service-level normalization before Pydantic validation. Frontend timeout handling wraps only the auto-start first-draft pipeline calls and reuses the existing error/retry UI. Migration verification should exercise Alembic from revision 0012 to head against a disposable database and only change env/migration code if the test exposes a real defect.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, Alembic, pytest, React, TypeScript, Vitest, React Testing Library.

---

## File Map

- Modify: `backend/app/llm/client.py` — extract JSON from markdown/code-fence/wrapper text and repair light JSON issues before returning a dict.
- Modify: `backend/app/world/service.py` — normalize light schema/type deviations before validating `WorldBriefExpansion`.
- Modify: `backend/tests/test_world_brief_expand.py` — add RED/GREEN tests for wrapped text, malformed JSON repair, light missing/type deviations, and unrepairable output.
- Modify: `backend/tests/test_migrations.py` — add Alembic 0012→0013 upgrade verification for import tables.
- Modify only if needed after RED: `backend/alembic/env.py` and/or `backend/alembic/versions/0013_add_import_node.py`.
- Modify: `frontend/src/studio/StudioPage.tsx` — timeout auto-start create/outline/write phases and surface retryable failure.
- Modify: `frontend/src/studio/StudioPage.test.tsx` — update infinite-pending tests into timeout/failure tests while keeping success coverage.

---

### Task 1: Backend brief expansion robust parsing and normalization

**Files:**
- Modify: `backend/tests/test_world_brief_expand.py`
- Modify: `backend/app/llm/client.py`
- Modify: `backend/app/world/service.py`

- [ ] **Step 1: Write failing backend tests**

Add tests that call `/worlds/brief/expand` through a fake LLM client returning:

1. A markdown/code-fenced JSON string with explanatory wrapper text.
2. JSON with light formatting defects such as trailing commas and single-quoted keys/strings.
3. A dict with defaultable missing fields and light type deviations, for example missing `tone_profile`, missing `relations`/`foreshadows`, scalar `current_goals`, and string numeric relation/foreshadow fields.
4. Unrepairable non-JSON text or payload with no usable characters still returning HTTP 502 `MODEL_RESPONSE_INVALID`.

- [ ] **Step 2: Run RED verification**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_world_brief_expand.py -q
```

Expected: new robustness tests fail because current code only accepts strict already-dict payloads from the fake/service path or strict `json.loads` in the real client path.

- [ ] **Step 3: Implement minimal parser and normalizer**

In `backend/app/llm/client.py`:

- Add a helper to strip code fences and extract the first balanced JSON object from response text.
- Add a helper to repair light JSON issues: remove trailing commas before `}`/`]`, and allow Python-literal style single-quoted structures via `ast.literal_eval` only after strict JSON parsing fails.
- Keep rejecting non-dict or unparseable output by raising `ValueError('MODEL_RESPONSE_INVALID')`.

In `backend/app/world/service.py`:

- Before `WorldBriefExpansion.model_validate`, recursively normalize a copy of model output:
  - If raw is a string, parse it with the same LLM-boundary parser or equivalent local helper.
  - Ensure `payload.tone_profile` defaults to `{}`.
  - Ensure `starter_assets.relations` and `starter_assets.foreshadows` default to `[]`.
  - Convert scalar `current_goals` to a one-item list.
  - Convert numeric strings for `intensity`, `urgency_level`, relation indexes, and related-character indexes to integers.
  - Keep required core fields required: title, genre_template, truth_canon, at least one character name/role.

- [ ] **Step 4: Run GREEN backend focused tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_world_brief_expand.py -q
```

Expected: all brief expansion tests pass, including unrepairable-output rejection.

---

### Task 2: Frontend auto-first-draft timeout and retryable UI

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write failing frontend tests**

Update the existing non-settling auto-start tests so they use fake timers and expect the UI to leave the indefinite pending state after the auto-start timeout:

- `createChapter` never settles: after advancing timers, expect alert text `自动生成第一章草稿失败，请检查章节目标后手动重试。`, notice title `世界已创建，第一章草稿尚未生成`, and button `重新创建第一章草稿`.
- `generateOutline` never settles after chapter creation: after advancing timers, expect the same retryable failure UI and no call to `writeChapter`.

Keep the existing success test asserting Writer Draft appears and approval is not called automatically.

- [ ] **Step 2: Run RED frontend focused test**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: new timeout tests fail because current auto-start awaits non-settling promises forever.

- [ ] **Step 3: Implement minimal timeout wrapper**

In `StudioPage.tsx`:

- Add a small `withAutoStartTimeout<T>(promise: Promise<T>): Promise<T>` helper with a timeout duration constant.
- Wrap only auto-start pipeline calls to `createChapterRequest`, `generateOutline`, `writeChapter`, and `refreshReviewStudioPanels` where indefinite pending can block user recovery.
- On timeout, throw so the existing catch sets the friendly retry error and existing retry button appears.
- Ensure timeout cleanup clears timers when the promise resolves or rejects.

- [ ] **Step 4: Run GREEN frontend focused test**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: Studio tests pass and success path still completes draft generation.

---

### Task 3: Alembic 0012 to 0013 upgrade verification and fix

**Files:**
- Modify: `backend/tests/test_migrations.py`
- Modify if needed: `backend/alembic/env.py`
- Modify if needed: `backend/alembic/versions/0013_add_import_node.py`

- [ ] **Step 1: Write failing or verifying migration test**

Add a pytest that creates a temporary SQLite database URL, constructs an Alembic `Config` for `/opt/WorldSim-Writer/backend/alembic.ini`, sets `script_location`, sets `sqlalchemy.url` to the temp DB, runs:

```python
command.upgrade(config, '0012_add_tags')
command.upgrade(config, 'head')
```

Then assert:

- `alembic_version.version_num == '0013_add_import_node'`
- `import_batches` exists
- `import_candidate_assets` exists

- [ ] **Step 2: Run RED/verification**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_migrations.py -q
```

Expected: if current migration is broken for local upgrade, the test fails. If it passes, keep the test as regression coverage and do not change env/migration code unnecessarily.

- [ ] **Step 3: Implement minimal migration fix only if the test fails**

If JSONB prevents portable migration verification or local SQLite-compatible upgrade, update `0013_add_import_node.py` to use a dialect-compatible JSON type pattern that still works for Postgres, or add a compilation shim in the test if production DB is Postgres-only and migration itself is correct.

If `env.py` ignores a test/CLI-provided URL, update it to preserve explicitly supplied `sqlalchemy.url` unless no override is present, while still defaulting to `get_settings().database_url` for normal local CLI use.

- [ ] **Step 4: Run migration GREEN test**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_migrations.py -q
```

Expected: migration tests pass and prove 0012→0013 creates import tables.

---

### Task 4: Required verification and commit

- [ ] **Step 1: Run backend focused tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_world_brief_expand.py -q
```

Expected: pass.

- [ ] **Step 2: Run relevant backend migration tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_migrations.py -q
```

Expected: pass.

- [ ] **Step 3: Run frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx --run
```

Expected: pass.

- [ ] **Step 4: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: pass.

- [ ] **Step 5: Run diff checks**

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer diff --cached --check
```

Expected: no output.

- [ ] **Step 6: Inspect status and commit**

```bash
git -C /opt/WorldSim-Writer status --short --branch
git -C /opt/WorldSim-Writer add backend/app/llm/client.py backend/app/world/service.py backend/tests/test_world_brief_expand.py backend/tests/test_migrations.py backend/alembic/env.py backend/alembic/versions/0013_add_import_node.py frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx docs/superpowers/plans/2026-06-07-e2e-brief-autodraft-migration-fixes.md
git -C /opt/WorldSim-Writer commit -m "fix: repair brief e2e loop"
```

Expected: commit on current branch `feat/import-node-p0`. Do not push and do not merge.
