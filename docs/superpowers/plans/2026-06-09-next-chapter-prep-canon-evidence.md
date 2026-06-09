# Next Chapter Prep Canon Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Story Bible/canon version and excerpt evidence to next-chapter prep API responses and UI.

**Architecture:** Reuse the current `World` row already loaded by `get_next_chapter_prep`. Add display-only fields to the response schema and frontend type, then render them in the existing `NextChapterPrepPanel` without changing execution context payloads or approval behavior.

**Tech Stack:** FastAPI/Pydantic, pytest, React/TypeScript, Vitest/Testing Library.

---

## File Structure

- Modify `backend/tests/test_narrative_control_center.py`: assert next-chapter prep includes current Story Bible version/excerpt.
- Modify `backend/app/narrative_control_center/schemas.py`: add additive response fields.
- Modify `backend/app/narrative_control_center/service.py`: return fields from `world.truth_canon_version` and `world.truth_canon`.
- Modify `frontend/src/world/NextChapterPrepPanel.test.tsx`: assert user-visible Story Bible evidence.
- Modify `frontend/src/api/types.ts`: add fields to `NextChapterPrepResponse`.
- Modify `frontend/src/world/NextChapterPrepPanel.tsx`: render the evidence.

---

### Task 1: Backend API evidence

- [ ] Add failing assertions to `test_next_chapter_prep_uses_high_priority_character_arc_progression_hint`:

```python
assert payload['truth_canon_version'] == 1
assert payload['truth_canon_excerpt'] == '青岚城由城主府、云河剑宗与地下商盟共同影响。灵脉衰退正在改变各方力量平衡，主角必须查清城主府叛乱传闻的真相。'
```

- [ ] Run RED:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_control_center.py::test_next_chapter_prep_uses_high_priority_character_arc_progression_hint -q
```

Expected: fail with missing `truth_canon_version` or `truth_canon_excerpt`.

- [ ] Add fields to `NextChapterPrepResponse`:

```python
truth_canon_version: int
truth_canon_excerpt: str
```

- [ ] Return those fields from `get_next_chapter_prep`:

```python
'truth_canon_version': world.truth_canon_version,
'truth_canon_excerpt': world.truth_canon.strip(),
```

- [ ] Run GREEN focused pytest.

---

### Task 2: Frontend panel evidence

- [ ] Add failing expectations in `NextChapterPrepPanel.test.tsx`:

```tsx
expect(screen.getByText('当前 Story Bible')).toBeInTheDocument();
expect(screen.getByText('正式设定版本：第 1 版')).toBeInTheDocument();
expect(screen.getByText('青岚城由城主府、云河剑宗与地下商盟共同影响。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('truth_canon_version');
expect(document.body).not.toHaveTextContent('truth_canon_excerpt');
```

- [ ] Run RED:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test -- src/world/NextChapterPrepPanel.test.tsx
```

Expected: fail because the Story Bible evidence is not rendered.

- [ ] Add `truth_canon_version` and `truth_canon_excerpt` to `NextChapterPrepResponse` in `frontend/src/api/types.ts`.

- [ ] Render a compact Story Bible evidence card in `NextChapterPrepPanel.tsx` using `labelWorldVersion(prep.truth_canon_version)`.

- [ ] Run GREEN focused Vitest.

---

### Task 3: Verify and commit

- [ ] Run backend related tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_control_center.py tests/test_narrative_pipeline.py -q
```

- [ ] Run frontend related tests and build:

```bash
npm --prefix /opt/WorldSim-Writer/frontend run test -- src/world/NextChapterPrepPanel.test.tsx src/world/chapterExecutionContext.test.ts src/studio/StudioPage.test.tsx
npm --prefix /opt/WorldSim-Writer/frontend run build
```

- [ ] Run diff checks:

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer diff --cached --check
```

- [ ] Commit only, no push or merge.
