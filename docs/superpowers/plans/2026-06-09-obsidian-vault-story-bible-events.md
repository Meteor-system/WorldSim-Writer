# Obsidian Vault Story Bible and Events Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Story Bible and per-event notes to the Markdown export vault without changing the export API contract.

**Architecture:** Extend the existing `backend/app/snapshot_export/service.py` Markdown renderers. Keep all existing files and response fields, then append `Story Bible.md`, `Events/Event-NNN.md`, and `Indexes/Events.md` with wikilinks from the existing README, world, and timeline notes.

**Tech Stack:** Python 3.13, FastAPI, pytest, existing snapshot export renderer and tests.

---

## File Structure

- Modify `backend/tests/test_snapshot_export.py`: add one regression test for Story Bible and event note vault navigation.
- Modify `backend/app/snapshot_export/service.py`: add Story Bible and event renderers, event paths, and wikilinks from existing notes.
- Create `docs/superpowers/specs/2026-06-09-obsidian-vault-story-bible-events-design.md`: design note.
- Create `docs/superpowers/plans/2026-06-09-obsidian-vault-story-bible-events.md`: this plan.

---

### Task 1: Add failing export-vault test

**Files:**
- Modify: `backend/tests/test_snapshot_export.py`

- [ ] **Step 1: Add the test**

Insert after `test_export_markdown_adds_obsidian_readme_and_index_files`:

```python
def test_export_markdown_adds_story_bible_and_event_notes_with_wikilinks(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'markdown-story-events@example.com')
    approved = approve_chapter(client, token, world_id, monkeypatch)

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    files_by_path = {file['path']: file['content'] for file in response.json()['files']}
    assert 'Story Bible.md' in files_by_path
    assert 'Events/Event-001.md' in files_by_path
    assert 'Indexes/Events.md' in files_by_path

    assert '[[Story Bible]]' in files_by_path['README.md']
    assert '[[Story Bible]]' in files_by_path['World.md']
    assert '[[Indexes/Events]]' in files_by_path['World.md']
    assert '[[Events/Event-001]]' in files_by_path['Timeline.md']
    assert '[[Events/Event-001]]' in files_by_path['Indexes/Timeline.md']
    assert '[[Events/Event-001]]' in files_by_path['Indexes/Events.md']

    story_bible = files_by_path['Story Bible.md']
    assert story_bible.startswith('---\n')
    assert 'worldsim_type: story_bible' in story_bible
    assert '## Truth Canon' in story_bible
    assert '## Story Arc' in story_bible
    assert '[[World]]' in story_bible

    event_note = files_by_path['Events/Event-001.md']
    assert event_note.startswith('---\n')
    assert 'worldsim_type: event' in event_note
    assert 'event_id:' in event_note
    assert 'Event ID:' not in event_note
    assert '[[World]]' in event_note
    assert '[[Chapters/Chapter-001]]' in event_note
    assert str(approved['id']) not in event_note.split('## Details', 1)[0]
```

- [ ] **Step 2: Run RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 python -m pytest tests/test_snapshot_export.py::test_export_markdown_adds_story_bible_and_event_notes_with_wikilinks -q
```

Expected: fail because `Story Bible.md`, `Events/Event-001.md`, and `Indexes/Events.md` are not yet exported.

---

### Task 2: Render Story Bible and event notes

**Files:**
- Modify: `backend/app/snapshot_export/service.py`

- [ ] **Step 1: Add Story Bible renderer**

Add `_story_bible_markdown(payload)` near `_readme_markdown`. It should include frontmatter `worldsim_type: story_bible`, link to `[[World]]`, include `## Truth Canon`, and include `## Story Arc`.

- [ ] **Step 2: Add event path and event note renderers**

Add `_event_markdown(event, sequence, chapter_paths)` and `_events_index_markdown(events, event_paths)`.

- [ ] **Step 3: Add wikilinks to existing notes**

Update `World.md`, `README.md`, `Timeline.md`, and `Indexes/Timeline.md` to link to `[[Story Bible]]`, `[[Indexes/Events]]`, and per-event notes where appropriate.

- [ ] **Step 4: Include files in `render_markdown_bundle`**

Reserve `Story Bible.md`, create `event_paths`, append event notes, and append `Indexes/Events.md` without removing or renaming existing files.

- [ ] **Step 5: Run GREEN**

Run the focused test again and expect pass.

---

### Task 3: Verify and commit

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run related backend tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 python -m pytest tests/test_snapshot_export.py -q
```

- [ ] **Step 2: Run full backend tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 python -m pytest -q
```

- [ ] **Step 3: Run diff checks and commit**

```bash
cd /opt/WorldSim-Writer
git diff --check
git add backend/app/snapshot_export/service.py backend/tests/test_snapshot_export.py docs/superpowers/specs/2026-06-09-obsidian-vault-story-bible-events-design.md docs/superpowers/plans/2026-06-09-obsidian-vault-story-bible-events.md
git diff --cached --check
git commit -m "feat: add story bible and event vault notes"
```

Do not push or merge.
