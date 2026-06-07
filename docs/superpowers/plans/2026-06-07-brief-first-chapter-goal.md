# Brief First Chapter Goal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this run. Do not use subagents, agents, code-review subagents, or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Carry the one-sentence world draft's first chapter goal into the post-creation auto-start Studio flow.

**Architecture:** Keep the world creation payload unchanged. Add an optional `first_chapter_goal` field to the brief expansion response, ask the backend LLM boundary to produce it, validate/sanitize it, and let the frontend pass it through `WorldCreationOptions` only when the user creates a world from a brief-filled form. `WorldPage` will use this goal for auto-start, with the existing overview-derived goal as fallback.

**Tech Stack:** FastAPI/Pydantic, React, TypeScript, Vitest, pytest.

---

## File Structure

- Modify `backend/app/world/schemas.py` — add optional validated `first_chapter_goal` to `WorldBriefExpansion`.
- Modify `backend/app/world/service.py` — request the field in brief-expansion prompt and include it in protected-term scanning.
- Modify `backend/app/llm/client.py` — include mock `first_chapter_goal` for local smoke mode.
- Modify `backend/tests/test_world_brief_expand.py` — RED coverage for returned goal and protected-term rejection in the goal.
- Modify `frontend/src/api/types.ts` — mirror optional `first_chapter_goal` and carry option.
- Modify `frontend/src/world/WorldCreationForm.tsx` — store the returned goal and pass it through creation options.
- Modify `frontend/src/world/WorldCreationForm.test.tsx` — assert brief-created submit includes the returned goal.
- Modify `frontend/src/world/WorldPage.tsx` — prefer option `firstChapterGoal` when auto-starting Studio.
- Modify `frontend/src/world/WorldPage.test.tsx` — assert Studio receives the specific returned first-chapter goal.

---

### Task 1: Add RED coverage for brief first-chapter goal

- [ ] **Step 1: Backend response test**

In `backend/tests/test_world_brief_expand.py`, make `FakeBriefLLMClient` return:

```python
'first_chapter_goal': '莉塔在命簿归档夜发现自己的死因栏是空白，并带走第一张空白命簿页。',
```

Then assert the response includes it.

- [ ] **Step 2: Backend safety test**

Add a test where the model returns a valid payload but `first_chapter_goal` contains a protected reference term. Expected response: `422 PROTECTED_REFERENCE_TERMS`, with no worlds or events persisted.

- [ ] **Step 3: Frontend form pass-through test**

Update the brief expansion mock in `WorldCreationForm.test.tsx` to include `first_chapter_goal`, and assert `onCreate` receives `{ autoStartFirstDraft: true, firstChapterGoal: '<goal>' }`.

- [ ] **Step 4: Frontend WorldPage auto-start test**

Update the existing brief-created world test in `WorldPage.test.tsx` so `expandWorldBrief` returns `first_chapter_goal`, then assert `initialChapterGoal` and `executionContext.goal` equal that exact goal.

- [ ] **Step 5: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 conda run -n worldsim pytest tests/test_world_brief_expand.py -v
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx --run
```

Expected: tests fail because the response field and frontend carry-through do not exist yet.

---

### Task 2: Implement the goal carry-through

- [ ] **Step 1: Add backend response field**

In `backend/app/world/schemas.py`, add:

```python
first_chapter_goal: str = ''
```

and validate it with the same strip behavior used for `rationale`.

- [ ] **Step 2: Update backend prompt and safety scan**

In `backend/app/world/service.py`, update the JSON contract and user instruction to request `first_chapter_goal`. Update `_protected_text_blob()` so protected-term detection covers both `payload` and `first_chapter_goal`.

- [ ] **Step 3: Update mock LLM response**

In `backend/app/llm/client.py`, include the same kind of `first_chapter_goal` in mock brief expansion output.

- [ ] **Step 4: Update frontend types**

In `frontend/src/api/types.ts`, add optional `first_chapter_goal?: string` to `WorldBriefExpandResponse` and optional `firstChapterGoal?: string` to `WorldCreationOptions`.

- [ ] **Step 5: Store and pass the goal in WorldCreationForm**

Add state for the brief-created first chapter goal. Reset it when selecting presets, applying seeds, canceling, or errors. On successful brief expansion, store `response.first_chapter_goal ?? ''`. On brief-created submit, call:

```ts
await onCreate(form, { autoStartFirstDraft: true, firstChapterGoal: briefFirstChapterGoal.trim() || undefined });
```

- [ ] **Step 6: Prefer the brief goal in WorldPage**

When `options.autoStartFirstDraft` is true, use `options.firstChapterGoal?.trim() || buildFirstChapterGoal(overview)` for `initialChapterGoal` and the manual execution context.

- [ ] **Step 7: Verify GREEN**

Run the same backend and frontend targeted tests. Expected: all pass.

---

### Task 3: Final verification and commit

- [ ] **Step 1: Run related loop regressions**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 conda run -n worldsim pytest tests/test_world_brief_expand.py -v
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx --run
```

- [ ] **Step 2: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

- [ ] **Step 3: Run diff checks, inspect status/log, and commit**

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add backend/app/world/schemas.py backend/app/world/service.py backend/app/llm/client.py backend/tests/test_world_brief_expand.py frontend/src/api/types.ts frontend/src/world/WorldCreationForm.tsx frontend/src/world/WorldCreationForm.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx docs/superpowers/plans/2026-06-07-brief-first-chapter-goal.md
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer status --short --branch
git -C /opt/WorldSim-Writer commit -m "fix: use brief first chapter goal"
git -C /opt/WorldSim-Writer status --short --branch
git -C /opt/WorldSim-Writer log --oneline -5
```

Expected: commit succeeds on `feat/import-node-p0`. Do not push. Do not merge.

---

## Inline Self-Review

- Spec coverage: closes the remaining Next-3 gap by using the one-sentence draft's first chapter goal rather than a generic derived goal.
- Scope check: no world creation payload or database change; the goal remains advisory launch context and does not write canon.
- TDD check: backend and frontend tests fail first on the missing field/carry-through, then pass after implementation.
- Placeholder scan: no TBD/TODO placeholders.
