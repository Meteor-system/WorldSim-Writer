# Obsidian Markdown Export Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing Markdown export into a more readable Obsidian-ready vault while preserving the current API contract and existing asserted paths.

**Architecture:** Keep all rendering inside `backend/app/snapshot_export/service.py`, matching the current snapshot/export service boundary. Add small Markdown helper functions for frontmatter, scalar/list formatting, and index pages, then enrich existing renderers and append additive files to the returned `files` list before ZIP creation.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic response schemas, Python stdlib `zipfile`, pytest backend integration tests, Vite/Vitest frontend verification for contract-adjacent confidence.

---

## File Structure

- Modify `backend/tests/test_snapshot_export.py`
  - Add failing tests for YAML frontmatter, additive Obsidian index/readme files, and ZIP/inline parity with additive files.
  - Keep existing compatibility tests intact.
- Modify `backend/app/snapshot_export/service.py`
  - Add Markdown formatting helpers.
  - Enrich existing files in place.
  - Add additive `README.md` and `Indexes/*.md` files.
- Create `docs/superpowers/specs/2026-06-09-obsidian-markdown-export-upgrade-design.md`
  - Design already written for the change.
- Create `docs/superpowers/plans/2026-06-09-obsidian-markdown-export-upgrade.md`
  - This implementation plan.

---

### Task 1: Add failing backend tests for vault metadata and additive files

**Files:**
- Modify: `backend/tests/test_snapshot_export.py`
- Test: `backend/tests/test_snapshot_export.py`

- [ ] **Step 1: Add tests after `test_export_markdown_returns_downloadable_obsidian_zip_bundle`**

Add these tests:

```python
def test_export_markdown_enriches_existing_files_with_obsidian_metadata(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'markdown-metadata@example.com')
    approved = approve_chapter(client, token, world_id, monkeypatch)

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    files_by_path = {file['path']: file['content'] for file in response.json()['files']}

    world_markdown = files_by_path['World.md']
    assert world_markdown.startswith('---\n')
    assert 'worldsim_type: world_index' in world_markdown
    assert f'world_id: {world_id}' in world_markdown
    assert 'tags:\n  - worldsim/world' in world_markdown
    assert '## Vault Navigation' in world_markdown
    assert '[[Indexes/Characters]]' in world_markdown
    assert '[[Indexes/Foreshadows]]' in world_markdown
    assert '[[Indexes/Chapters]]' in world_markdown

    chapter_markdown = files_by_path['Chapters/Chapter-001.md']
    assert chapter_markdown.startswith('---\n')
    assert 'worldsim_type: chapter' in chapter_markdown
    assert f"chapter_id: {approved['chapter_id']}" in chapter_markdown
    assert 'chapter_number: 1' in chapter_markdown
    assert 'tags:\n  - worldsim/chapter' in chapter_markdown
    assert '[[World]]' in chapter_markdown
    assert approved['approved_content'] in chapter_markdown


def test_export_markdown_adds_obsidian_readme_and_index_files(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'markdown-indexes@example.com')
    approve_chapter(client, token, world_id, monkeypatch)

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    files_by_path = {file['path']: file['content'] for file in response.json()['files']}
    assert 'World.md' in files_by_path
    assert 'Relations.md' in files_by_path
    assert 'Timeline.md' in files_by_path
    assert 'Chapters/Chapter-001.md' in files_by_path
    assert 'README.md' in files_by_path
    assert 'Indexes/Characters.md' in files_by_path
    assert 'Indexes/Foreshadows.md' in files_by_path
    assert 'Indexes/Chapters.md' in files_by_path
    assert 'Indexes/Timeline.md' in files_by_path

    readme = files_by_path['README.md']
    assert readme.startswith('---\n')
    assert 'worldsim_type: vault_readme' in readme
    assert 'Open [[World]] first.' in readme
    assert 'The original API contract is preserved' in readme

    character_index = files_by_path['Indexes/Characters.md']
    assert character_index.startswith('---\n')
    assert 'worldsim_type: character_index' in character_index
    assert '| Character | Role | Status | Goals |' in character_index
    assert '[[Characters/' in character_index

    timeline_index = files_by_path['Indexes/Timeline.md']
    assert timeline_index.startswith('---\n')
    assert 'worldsim_type: timeline_index' in timeline_index
    assert '[[Timeline]]' in timeline_index
```

- [ ] **Step 2: Run new tests and verify they fail**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py::test_export_markdown_enriches_existing_files_with_obsidian_metadata tests/test_snapshot_export.py::test_export_markdown_adds_obsidian_readme_and_index_files -v'
```

Expected: both tests fail because existing Markdown files do not have frontmatter and additive index/readme files do not exist.

---

### Task 2: Implement Markdown helpers and enrich existing files

**Files:**
- Modify: `backend/app/snapshot_export/service.py`
- Test: `backend/tests/test_snapshot_export.py`

- [ ] **Step 1: Add helper functions near `_markdown_value`**

Add helpers to format YAML frontmatter safely and compactly:

```python
def _yaml_scalar(value: Any) -> str:
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, int | float):
        return str(value)
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def _frontmatter(data: dict[str, Any]) -> str:
    lines = ['---']
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f'{key}:')
            if value:
                lines.extend(f'  - {_yaml_scalar(item)}' for item in value)
            else:
                lines.append('  []')
        else:
            lines.append(f'{key}: {_yaml_scalar(value)}')
    lines.append('---')
    lines.append('')
    return '\n'.join(lines)


def _bullet_or_empty(items: list[str]) -> list[str]:
    return [f'- {item}' for item in items] if items else ['- 暂无']
```

- [ ] **Step 2: Enrich existing renderers with frontmatter and navigation**

Update these functions without changing their path callers:

- `_world_markdown(...)`: prepend frontmatter with `worldsim_type: world_index`, `world_id`, `world_version`, `truth_canon_version`, `status`, `title`, and `tags: ['worldsim/world']`; add a `## Vault Navigation` section linking to `README`, `Relations`, `Timeline`, and all `Indexes/*` pages before `## Truth Canon`.
- `_character_markdown(...)`: prepend frontmatter with `worldsim_type: character`, `character_id`, `name`, `role`, `status`, `destiny_flag`, and `tags: ['worldsim/character']`; add `[[World]]` backlink near top.
- `_foreshadow_markdown(...)`: prepend frontmatter with `worldsim_type: foreshadow`, `foreshadow_id`, `title`, `status`, `urgency`, `source_chapter_id`, `related_character_ids`, and `tags: ['worldsim/foreshadow']`; add `[[World]]` backlink near top.
- `_relations_markdown(...)`: prepend frontmatter with `worldsim_type: relations`, `relation_count`, and `tags: ['worldsim/relations']`; add `[[World]]` backlink near top.
- `_chapter_markdown(...)`: prepend frontmatter with `worldsim_type: chapter`, `chapter_id`, `title`, `status`, `approved_version`, `base_world_version`, `chapter_number`, and `tags: ['worldsim/chapter']`; add `[[World]]` backlink near top.
- `_events_markdown(...)`: prepend frontmatter with `worldsim_type: timeline`, `event_count`, and `tags: ['worldsim/timeline']`; add `[[World]]` backlink and an `## Summary` section before the event table.

- [ ] **Step 3: Run the metadata test and verify it passes or shows only additive-file failures**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py::test_export_markdown_enriches_existing_files_with_obsidian_metadata -v'
```

Expected: PASS after in-place metadata changes.

---

### Task 3: Add additive README and index files

**Files:**
- Modify: `backend/app/snapshot_export/service.py`
- Test: `backend/tests/test_snapshot_export.py`

- [ ] **Step 1: Add additive file renderers before `render_markdown_bundle`**

Add renderers:

```python
def _readme_markdown(payload: dict[str, Any]) -> str:
    world = payload['world']
    return _frontmatter(
        {
            'worldsim_type': 'vault_readme',
            'world_id': world['id'],
            'world_version': world['world_version'],
            'title': world['title'],
            'tags': ['worldsim/readme'],
        }
    ) + '\n'.join(
        [
            f"# {world['title']} Markdown Vault",
            '',
            'Open [[World]] first.',
            '',
            '## Main files',
            '',
            '- [[World]] — canonical world overview and vault index.',
            '- [[Relations]] — character relationship table.',
            '- [[Timeline]] — event history exported from WorldSim.',
            '- [[Indexes/Characters]] — character directory.',
            '- [[Indexes/Foreshadows]] — foreshadow ledger directory.',
            '- [[Indexes/Chapters]] — approved chapter directory.',
            '- [[Indexes/Timeline]] — timeline helper page.',
            '',
            'The original API contract is preserved: this vault is also returned as inline `files` and a base64 ZIP archive.',
            '',
        ]
    )
```

Also add `_characters_index_markdown`, `_foreshadows_index_markdown`, `_chapters_index_markdown`, and `_timeline_index_markdown` that generate frontmatter plus tables linking to existing file paths.

- [ ] **Step 2: Append additive files in `render_markdown_bundle`**

After appending `Timeline.md`, append:

```python
    files.extend(
        [
            {'path': 'README.md', 'content': _readme_markdown(payload)},
            {'path': 'Indexes/Characters.md', 'content': _characters_index_markdown(payload['characters'], character_paths)},
            {'path': 'Indexes/Foreshadows.md', 'content': _foreshadows_index_markdown(payload['foreshadows'], foreshadow_paths)},
            {'path': 'Indexes/Chapters.md', 'content': _chapters_index_markdown(payload['approved_chapters'], chapter_paths)},
            {'path': 'Indexes/Timeline.md', 'content': _timeline_index_markdown(payload['events'])},
        ]
    )
```

- [ ] **Step 3: Run additive file test and verify it passes**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py::test_export_markdown_adds_obsidian_readme_and_index_files -v'
```

Expected: PASS.

---

### Task 4: Run compatibility-focused backend tests

**Files:**
- Test: `backend/tests/test_snapshot_export.py`

- [ ] **Step 1: Run snapshot export tests**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py -v'
```

Expected: PASS. Existing tests should confirm current paths remain, ZIP contents match inline files, path sanitization still works, export stays read-only, and auth/ownership behavior remains intact.

- [ ] **Step 2: Fix any regression using the smallest code change**

If a test fails due to exact content expectations, preserve the older visible text and add new metadata around it instead of removing old sections.

---

### Task 5: Run full verification and commit

**Files:**
- All modified files

- [ ] **Step 1: Run full backend tests**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest -v'
```

Expected: PASS.

- [ ] **Step 2: Run frontend tests and build for API-contract confidence**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: both PASS. No frontend code should need modification because the API response shape is unchanged.

- [ ] **Step 3: Check whitespace errors**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 4: Inspect final diff**

Run:

```bash
git status --short
git diff -- backend/app/snapshot_export/service.py backend/tests/test_snapshot_export.py docs/superpowers/specs/2026-06-09-obsidian-markdown-export-upgrade-design.md docs/superpowers/plans/2026-06-09-obsidian-markdown-export-upgrade.md
```

Expected: diff only contains the export upgrade, tests, and planning docs.

- [ ] **Step 5: Commit**

Run:

```bash
git add backend/app/snapshot_export/service.py backend/tests/test_snapshot_export.py docs/superpowers/specs/2026-06-09-obsidian-markdown-export-upgrade-design.md docs/superpowers/plans/2026-06-09-obsidian-markdown-export-upgrade.md
git commit -m "feat: enrich markdown vault export"
```

Expected: commit succeeds. Do not push or merge.

---

## Self-review

- Spec coverage: API contract preserved; current paths preserved; richer frontmatter/readability added; additive files added; export remains read-only; targeted tests added first; full verification and commit included.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: helper names and response fields match existing Python service and test files.
