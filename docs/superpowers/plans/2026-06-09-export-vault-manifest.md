# Export Vault Manifest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a top-level `Manifest.md` to Markdown exports so beta testers can verify vault contents and API compatibility evidence from inside the archive.

**Architecture:** Extend the existing `backend/app/snapshot_export/service.py` Markdown renderer. Keep all existing files and response fields, reserve `Manifest.md`, append the manifest after indexes are assembled, and link it from existing navigation notes.

**Tech Stack:** Python 3.13, FastAPI, pytest, existing snapshot export renderer.

---

## File Structure

- Modify `backend/tests/test_snapshot_export.py`: add one failing regression test for the manifest note.
- Modify `backend/app/snapshot_export/service.py`: add manifest renderer, reserve `Manifest.md`, link from README/World, and include the new file.
- Create `docs/superpowers/specs/2026-06-09-export-vault-manifest-design.md`: design note.
- Create `docs/superpowers/plans/2026-06-09-export-vault-manifest.md`: this plan.

---

### Task 1: Add failing manifest test

**Files:**
- Modify: `backend/tests/test_snapshot_export.py`

- [ ] **Step 1: Add the test**

Insert after `test_export_markdown_adds_obsidian_readme_and_index_files`:

```python
def test_export_markdown_adds_vault_manifest_for_archive_verification(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'markdown-manifest@example.com')
    approve_chapter(client, token, world_id, monkeypatch)

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    files_by_path = {file['path']: file['content'] for file in response.json()['files']}
    assert 'Manifest.md' in files_by_path
    assert '[[Manifest]]' in files_by_path['README.md']
    assert '[[Manifest]]' in files_by_path['World.md']

    manifest = files_by_path['Manifest.md']
    assert manifest.startswith('---\n')
    assert 'worldsim_type: vault_manifest' in manifest
    assert f'world_id: {world_id}' in manifest
    assert f"file_count: {len(files_by_path)}" in manifest
    assert '## Archive Metadata' in manifest
    assert 'archive_format: zip' in manifest
    assert 'archive_encoding: base64' in manifest
    assert 'files_are_inline: true' in manifest
    assert '## Content Counts' in manifest
    assert '- Approved Chapters: 1' in manifest
    assert '## File Inventory' in manifest
    assert '- [[World]] `World.md`' in manifest
    assert '- [[Story Bible]] `Story Bible.md`' in manifest
    assert '- [[Chapters/Chapter-001]] `Chapters/Chapter-001.md`' in manifest
    assert '- [[Events/Event-001]] `Events/Event-001.md`' in manifest
```

- [ ] **Step 2: Run RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 python -m pytest tests/test_snapshot_export.py::test_export_markdown_adds_vault_manifest_for_archive_verification -q
```

Expected: fail because `Manifest.md` does not exist.

---

### Task 2: Render and link Manifest.md

**Files:**
- Modify: `backend/app/snapshot_export/service.py`

- [ ] **Step 1: Add manifest links**

Add `- [[Manifest]]` to `_world_markdown()` vault navigation and `_readme_markdown()` main files.

- [ ] **Step 2: Add `_manifest_markdown(payload, files)`**

Create a helper that receives the payload and final file list, renders frontmatter with `worldsim_type: vault_manifest`, and emits archive metadata, content counts, preserved API contract fields, and a file inventory. For Markdown files, use `[[{_wiki_path(path)}]]` followed by the literal path in backticks.

- [ ] **Step 3: Include manifest in `render_markdown_bundle()`**

Reserve `Manifest.md` in `used_paths`. Build existing files as before, then append:

```python
files.append({'path': 'Manifest.md', 'content': _manifest_markdown(payload, [*files, {'path': 'Manifest.md'}])})
```

This lets `file_count` and file inventory include the manifest itself.

- [ ] **Step 4: Run GREEN**

Run the focused test again and expect pass.

---

### Task 3: Verify and commit

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run related export tests**

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
git add backend/app/snapshot_export/service.py backend/tests/test_snapshot_export.py docs/superpowers/specs/2026-06-09-export-vault-manifest-design.md docs/superpowers/plans/2026-06-09-export-vault-manifest.md
git diff --cached --check
git commit -m "feat: add markdown vault manifest"
```

Do not push or merge.
