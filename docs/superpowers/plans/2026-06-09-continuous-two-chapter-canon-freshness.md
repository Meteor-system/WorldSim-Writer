# Continuous Two-Chapter Canon Freshness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove chapter 2 generation in the existing continuous backend E2E path uses a Story Bible/canon edit made after chapter 1 approval.

**Architecture:** Keep this as a test-only MVP/Beta hardening change unless the test exposes a production bug. Strengthen the existing `test_continuous_two_chapters_use_latest_context_and_stale_third_draft_is_blocked` flow by inserting a canon update after chapter 1 approval, then assert the second captured LLM prompt uses the updated canon and latest world version while preserving prior continuity and stale-approval assertions.

**Tech Stack:** Python 3.13, pytest, FastAPI TestClient, SQLAlchemy test DB, existing narrative service monkeypatch LLM client.

---

## File Structure

- Modify `backend/tests/test_narrative_pipeline.py`: strengthen the existing continuous two-chapter integration test.
- Create `docs/superpowers/specs/2026-06-09-continuous-two-chapter-canon-freshness-design.md`: design note.
- Create `docs/superpowers/plans/2026-06-09-continuous-two-chapter-canon-freshness.md`: this plan.

---

### Task 1: Add the failing canon-freshness expectation

**Files:**
- Modify: `backend/tests/test_narrative_pipeline.py`
- Test: `backend/tests/test_narrative_pipeline.py`

- [ ] **Step 1: Add a distinctive canon expectation before changing setup**

In `test_continuous_two_chapters_use_latest_context_and_stale_third_draft_is_blocked`, after `second_prompt = ...`, add:

```python
    updated_canon = '第二章前设定：城主府外墙刻着三枚潮汐符印，只有湿信能显影。'
    assert updated_canon in second_prompt
```

Do not yet call the canon update endpoint.

- [ ] **Step 2: Run the focused test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_pipeline.py::test_continuous_two_chapters_use_latest_context_and_stale_third_draft_is_blocked -q
```

Expected: FAIL because `updated_canon` is not in the second prompt yet.

---

### Task 2: Add the canon edit to the continuous flow

**Files:**
- Modify: `backend/tests/test_narrative_pipeline.py`

- [ ] **Step 1: Insert the canon edit after chapter 1 approval**

Immediately after:

```python
    assert client.post(f"/chapters/{first_draft['chapter_id']}/approve", headers=auth(token)).status_code == 200
```

add:

```python
    updated_canon = '第二章前设定：城主府外墙刻着三枚潮汐符印，只有湿信能显影。'
    canon_update = client.put(
        f'/worlds/{world_id}/canon',
        headers=auth(token),
        json={'truth_canon': updated_canon, 'edit_reason': '第二章前更新 Story Bible'},
    )
    assert canon_update.status_code == 200
```

Remove the duplicate `updated_canon = ...` assignment near the prompt assertions if Task 1 placed it there.

- [ ] **Step 2: Update second prompt assertions**

Replace the old default canon assertion:

```python
    assert '世界设定：青岚城由城主府、云河剑宗与地下商盟共同影响。' in second_prompt
    assert '世界版本：2' in second_prompt
```

with:

```python
    assert f'世界设定：{updated_canon}' in second_prompt
    assert '世界版本：3' in second_prompt
```

- [ ] **Step 3: Update expected post-chapter-2 world version**

Replace:

```python
    assert overview['world_version'] == 3
```

with:

```python
    assert overview['world_version'] == 4
```

The version is now 4 because chapter 1 approval moves 1→2, the canon edit moves 2→3, and chapter 2 approval moves 3→4.

- [ ] **Step 4: Run the focused test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_pipeline.py::test_continuous_two_chapters_use_latest_context_and_stale_third_draft_is_blocked -q
```

Expected: PASS.

---

### Task 3: Verify related backend coverage

**Files:**
- Verify `backend/tests/test_narrative_pipeline.py`
- Verify `backend/tests/test_story_bible_management.py`
- Verify full backend suite

- [ ] **Step 1: Run related tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_pipeline.py tests/test_story_bible_management.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full backend tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest -q
```

Expected: PASS.

---

### Task 4: Diff check and commit

**Files:**
- Modified and created files above.

- [ ] **Step 1: Run diff check**

Run:

```bash
cd /opt/WorldSim-Writer && git diff --check
```

Expected: no output and exit 0.

- [ ] **Step 2: Stage and commit only**

Run:

```bash
cd /opt/WorldSim-Writer
git status --short
git add backend/tests/test_narrative_pipeline.py docs/superpowers/specs/2026-06-09-continuous-two-chapter-canon-freshness-design.md docs/superpowers/plans/2026-06-09-continuous-two-chapter-canon-freshness.md
git diff --cached --check
git commit -m "test: cover continuous chapter canon freshness"
```

Expected: commit succeeds. Do not push or merge.
