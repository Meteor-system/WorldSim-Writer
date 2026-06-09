# Export Chapter Author Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. For this session, the user explicitly requires inline execution with no subagents/agents/code-review subagent.

**Goal:** Preserve chapter goal, context summary, and review hints in exported Markdown chapter notes.

**Architecture:** Reuse the approved chapter and approved draft data already persisted by the narrative flow. Add a small helper to find the approved draft for each approved chapter, include author-context fields in the archive payload, and render them inside each chapter note before the approved prose.

**Tech Stack:** Python, FastAPI service layer, SQLAlchemy relationships, pytest, Markdown/Obsidian vault files.

---

## File Structure

- Modify `backend/tests/test_snapshot_export.py`: add failing assertions for chapter goal, context summary, and review hints in an exported chapter note.
- Modify `backend/app/snapshot_export/service.py`: include approved draft author context in archive payload and render it in chapter Markdown.
- Create this plan and matching design doc.

---

### Task 1: Add failing chapter author context export assertions

- [ ] In `backend/tests/test_snapshot_export.py`, update `test_export_markdown_enriches_existing_files_with_obsidian_metadata` after the existing chapter note metadata assertions to require author context:

```python
    assert '- Chapter Goal: 推进档案门廊线索' in chapter_markdown
    assert '## Context Summary' in chapter_markdown
    assert '林砚发现门廊中的玉佩线索。' in chapter_markdown
    assert '## Review Hints' in chapter_markdown
    assert '- 确认玉佩线索是否进入伏笔台账' in chapter_markdown
    assert chapter_markdown.index('## Context Summary') < chapter_markdown.index('## Content')
    assert chapter_markdown.index('## Review Hints') < chapter_markdown.index('## Content')
```

- [ ] Run RED:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_snapshot_export.py::test_export_markdown_enriches_existing_files_with_obsidian_metadata -q
```

Expected: fail because chapter Markdown currently lacks `Chapter Goal`, `Context Summary`, and `Review Hints`.

---

### Task 2: Add approved draft author context to archive payload

- [ ] In `backend/app/snapshot_export/service.py`, add helper near `build_world_archive_payload()`:

```python
def _approved_draft_for_chapter(chapter: Chapter):
    return next((draft for draft in chapter.drafts if draft.draft_version == chapter.approved_version), None)
```

- [ ] Replace the approved chapter list comprehension in `build_world_archive_payload()` with a loop that includes the approved draft fields:

```python
    approved_chapter_payloads = []
    for chapter in approved_chapters:
        approved_draft = _approved_draft_for_chapter(chapter)
        approved_chapter_payloads.append(
            {
                'id': chapter.id,
                'title': chapter.title,
                'status': chapter.status,
                'approved_version': chapter.approved_version,
                'base_world_version': chapter.base_world_version,
                'chapter_goal': chapter.chapter_goal,
                'context_summary': approved_draft.context_summary if approved_draft else '',
                'review_hints': deepcopy(approved_draft.review_hints) if approved_draft else [],
                'approved_content': chapter.approved_content,
            }
        )
```

- [ ] Use `approved_chapter_payloads` in the returned payload:

```python
'approved_chapters': approved_chapter_payloads,
```

---

### Task 3: Render chapter author context in Markdown

- [ ] In `_chapter_markdown()`, add the chapter goal metadata after base world version:

```python
            f"- Chapter Goal: {chapter.get('chapter_goal') or ''}",
```

- [ ] Add sections before `## Content`:

```python
            '## Context Summary',
            '',
            chapter.get('context_summary') or '暂无',
            '',
            '## Review Hints',
            '',
            *_markdown_list(chapter.get('review_hints') or []),
            '',
```

- [ ] Add helper near `_markdown_cell()`:

```python
def _markdown_list(items: list[Any]) -> list[str]:
    return [f"- {_markdown_value(item)}" for item in items] if items else ['- 暂无']
```

- [ ] Run GREEN focused pytest:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_snapshot_export.py::test_export_markdown_enriches_existing_files_with_obsidian_metadata -q
```

Expected: pass.

---

### Task 4: Verify export slice and commit

- [ ] Run related snapshot export tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_snapshot_export.py -q
```

- [ ] Run full backend tests because backend export serialization changed:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
```

- [ ] Skip frontend tests/build and state why: no frontend code or typed API contract changed.

- [ ] Run diff checks:

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add backend/app/snapshot_export/service.py backend/tests/test_snapshot_export.py docs/superpowers/specs/2026-06-09-export-chapter-author-context-design.md docs/superpowers/plans/2026-06-09-export-chapter-author-context.md
git -C /opt/WorldSim-Writer diff --cached --check
```

- [ ] Commit only:

```bash
git -C /opt/WorldSim-Writer commit -m "feat: export chapter author context"
```

Do not push or merge.
