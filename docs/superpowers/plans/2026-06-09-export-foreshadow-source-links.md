# Export Foreshadow Source Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. For this session, the user explicitly requires inline execution with no subagents/agents/code-review subagent.

**Goal:** Add Obsidian wikilinks from exported foreshadow notes to their approved source chapter notes.

**Architecture:** Reuse the existing deterministic chapter path map created by `render_markdown_bundle`. Thread that map into foreshadow note rendering and format `Source Chapter` as a wikilink only when the source chapter exists in the exported approved chapter set; otherwise preserve the existing raw ID/blank fallback.

**Tech Stack:** Python, FastAPI service layer, pytest, Markdown/Obsidian wikilinks.

---

## File Structure

- Modify `backend/tests/test_snapshot_export.py`: add failing assertion to existing export wikilink test for foreshadow source-chapter links.
- Modify `backend/app/snapshot_export/service.py`: pass `chapter_paths` into foreshadow rendering and add source chapter link formatting.
- Create this plan and matching design doc.

---

### Task 1: Add failing foreshadow source chapter export test

- [ ] In `backend/tests/test_snapshot_export.py`, update `test_export_markdown_adds_story_bible_and_event_notes_with_wikilinks` after `approved = approve_chapter(...)` to set the first current foreshadow's `source_chapter_id` to the approved chapter ID:

```python
    world = db_session.get(World, world_id)
    world.current_foreshadows = [world.current_foreshadows[0] | {'source_chapter_id': approved['id']}]
    db_session.commit()
```

- [ ] In the same test, after `event_note` assertions, assert the exported foreshadow note links to the chapter note:

```python
    foreshadow_note = next(content for path, content in files_by_path.items() if path.startswith('Foreshadows/'))
    assert '- Source Chapter: [[Chapters/Chapter-001]]' in foreshadow_note
```

- [ ] Run RED:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_snapshot_export.py::test_export_markdown_adds_story_bible_and_event_notes_with_wikilinks -q
```

Expected: fail because the foreshadow note renders the raw approved chapter ID instead of `[[Chapters/Chapter-001]]`.

---

### Task 2: Render foreshadow source chapter wikilinks

- [ ] In `backend/app/snapshot_export/service.py`, add helper near `_event_chapter_link`:

```python
def _foreshadow_source_chapter_link(foreshadow: dict[str, Any], chapter_paths: dict[int, str]) -> str:
    source_chapter_id = foreshadow.get('source_chapter_id')
    if source_chapter_id in chapter_paths:
        return f"[[{_wiki_path(chapter_paths[source_chapter_id])}]]"
    return str(source_chapter_id or '')
```

- [ ] Change `_foreshadow_markdown` signature to accept `chapter_paths`:

```python
def _foreshadow_markdown(
    foreshadow: dict[str, Any],
    character_by_id: dict[int, dict[str, Any]],
    character_paths: dict[int, str],
    chapter_paths: dict[int, str],
) -> str:
```

- [ ] Inside `_foreshadow_markdown`, compute:

```python
    source_chapter_link = _foreshadow_source_chapter_link(foreshadow, chapter_paths)
```

- [ ] Replace the `Source Chapter` line with:

```python
            f"- Source Chapter: {source_chapter_link}",
```

- [ ] Update the call in `render_markdown_bundle`:

```python
'content': _foreshadow_markdown(foreshadow, character_by_id, character_paths, chapter_paths),
```

- [ ] Run GREEN focused pytest:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_snapshot_export.py::test_export_markdown_adds_story_bible_and_event_notes_with_wikilinks -q
```

Expected: pass.

---

### Task 3: Verify export slice and commit

- [ ] Run related snapshot export tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_snapshot_export.py -q
```

- [ ] Run full backend tests because export serialization changed:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
```

- [ ] Skip frontend tests/build and state why: no frontend code or API contract changed.

- [ ] Run diff checks:

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add backend/app/snapshot_export/service.py backend/tests/test_snapshot_export.py docs/superpowers/specs/2026-06-09-export-foreshadow-source-links-design.md docs/superpowers/plans/2026-06-09-export-foreshadow-source-links.md
git -C /opt/WorldSim-Writer diff --cached --check
```

- [ ] Commit only:

```bash
git -C /opt/WorldSim-Writer commit -m "feat: link foreshadow sources in export"
```

Do not push or merge.
