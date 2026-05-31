# MVP13 Obsidian / Markdown Export 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline for this repository because the user explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a downloadable Obsidian-friendly Markdown export bundle for formal world canon, characters, relations, foreshadows, approved chapters, and timeline.

**Architecture:** Extend the existing `snapshot_export` backend module instead of adding a parallel exporter. Keep the JSON `files` preview response, add backend-generated ZIP metadata (`archive_filename`, `archive_base64`), harden Markdown path generation, and update `WorldArchivePanel` to prepare a browser download from the returned archive.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Python standard-library `zipfile`/`base64`, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File map

- Modify `backend/app/snapshot_export/schemas.py`
  - Add `archive_filename` and `archive_base64` to `WorldMarkdownExportResponse`.
- Modify `backend/app/snapshot_export/service.py`
  - Add safe path segment helpers, duplicate path handling, sequence chapter filenames, richer Markdown renderers, and ZIP encoding.
- Modify `backend/tests/test_snapshot_export.py`
  - Add RED tests for ZIP bundle metadata, Obsidian path structure, ZIP/file parity, filename sanitization, collision handling, and approved-only export.
- Modify `frontend/src/api/types.ts`
  - Add `archive_filename` and `archive_base64` to `WorldMarkdownExportResponse`.
- Modify `frontend/src/api/client.test.ts`
  - Add RED API helper assertion for `exportWorldArchiveMarkdown`.
- Modify `frontend/src/world/WorldArchivePanel.tsx`
  - Add base64-to-Blob download helper, filename display, and retry download button.
- Modify `frontend/src/world/WorldArchivePanel.test.tsx`
  - Add RED UI test for filename display and download link/button behavior.

## Task 1: Backend export ZIP contract and Obsidian path structure

**Files:**
- Modify: `backend/tests/test_snapshot_export.py`
- Modify: `backend/app/snapshot_export/schemas.py`
- Modify: `backend/app/snapshot_export/service.py`

- [ ] **Step 1: Write failing backend test for ZIP bundle and path structure**

Add this test to `backend/tests/test_snapshot_export.py` near the existing markdown export tests:

```python
import base64
from io import BytesIO
from zipfile import ZipFile


def test_export_markdown_returns_downloadable_obsidian_zip_bundle(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'markdown-zip@example.com')
    approved = approve_chapter(client, token, world_id, monkeypatch)

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['archive_filename'].endswith('-v2-markdown.zip')
    assert payload['archive_base64']

    files_by_path = {file['path']: file['content'] for file in payload['files']}
    assert 'World.md' in files_by_path
    assert 'Relations.md' in files_by_path
    assert 'Timeline.md' in files_by_path
    assert 'Timeline/Events.md' not in files_by_path
    assert 'Chapters/Chapter-001.md' in files_by_path
    assert approved['approved_content'] in files_by_path['Chapters/Chapter-001.md']
    assert 'World Version: 2' in files_by_path['World.md']
    assert 'Truth Canon Version:' in files_by_path['World.md']
    assert '[[Timeline]]' in files_by_path['World.md']

    archive_bytes = base64.b64decode(payload['archive_base64'])
    with ZipFile(BytesIO(archive_bytes)) as archive:
        archived_paths = set(archive.namelist())
        assert archived_paths == set(files_by_path)
        assert archive.read('Chapters/Chapter-001.md').decode('utf-8') == files_by_path['Chapters/Chapter-001.md']
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py::test_export_markdown_returns_downloadable_obsidian_zip_bundle -v
```

Expected: FAIL because `archive_filename` / `archive_base64` are missing and current paths use `Timeline/Events.md` plus chapter database IDs.

- [ ] **Step 3: Implement minimal backend ZIP response and path changes**

In `backend/app/snapshot_export/schemas.py`, update `WorldMarkdownExportResponse`:

```python
class WorldMarkdownExportResponse(BaseModel):
    world_id: int
    world_version: int
    generated_at: datetime
    archive_filename: str
    archive_base64: str
    files: list[MarkdownExportFile]
```

In `backend/app/snapshot_export/service.py`:

- Import `base64`, `BytesIO`, and `ZipFile`.
- Change chapter paths to `Chapters/Chapter-001.md`, `Chapter-002.md`, etc.
- Change timeline path to `Timeline.md`.
- Add `_zip_markdown_files(files)` and `_archive_filename(world)`.
- Include `archive_filename` and `archive_base64` in `export_world_markdown()`.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py::test_export_markdown_returns_downloadable_obsidian_zip_bundle -v
```

Expected: PASS.

## Task 2: Backend filename sanitization, de-duplication, and richer Markdown content

**Files:**
- Modify: `backend/tests/test_snapshot_export.py`
- Modify: `backend/app/snapshot_export/service.py`

- [ ] **Step 1: Write failing backend test for safe duplicate paths**

Add this test to `backend/tests/test_snapshot_export.py`:

```python
def test_export_markdown_sanitizes_and_deduplicates_markdown_paths(client, db_session):
    token, world_id = register_and_create_world(client, 'markdown-sanitize@example.com')
    world = db_session.get(World, world_id)
    world.title = '青岚/城?'
    world.current_characters = [
        {
            'id': 101,
            'name': '林/砚?',
            'role_type': 'protagonist',
            'status': 'active',
            'public_profile': {'origin': '雨巷'},
            'hidden_traits': {'secret': '玉佩'},
            'destiny_flag': None,
            'current_goals': ['追查湿信'],
        },
        {
            'id': 102,
            'name': '林:砚',
            'role_type': 'ally',
            'status': 'active',
            'public_profile': {},
            'hidden_traits': {},
            'destiny_flag': None,
            'current_goals': [],
        },
    ]
    world.current_relations = [
        {
            'id': 201,
            'source_character_id': 101,
            'target_character_id': 102,
            'relation_type': 'mirror',
            'intensity': 3,
            'visibility': 'private',
        }
    ]
    world.current_foreshadows = [
        {
            'id': 301,
            'source_chapter_id': None,
            'title': '../裂纹/玉佩?',
            'description': '玉佩裂纹扩散。',
            'foreshadow_type': 'item',
            'status': 'advanced',
            'urgency_level': 5,
            'related_character_ids': [101],
            'expected_resolution_window': '第3章',
        },
        {
            'id': 302,
            'source_chapter_id': None,
            'title': '..:裂纹:玉佩',
            'description': '重复标题用于测试去重。',
            'foreshadow_type': 'item',
            'status': 'planted',
            'urgency_level': 4,
            'related_character_ids': [102],
            'expected_resolution_window': None,
        },
    ]
    db_session.commit()

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    paths = [file['path'] for file in payload['files']]
    assert payload['archive_filename'] == 'WorldSim-青岚-城-v1-markdown.zip'
    assert 'Characters/林-砚.md' in paths
    assert 'Characters/林-砚-2.md' in paths
    assert 'Foreshadows/裂纹-玉佩.md' in paths
    assert 'Foreshadows/裂纹-玉佩-2.md' in paths
    assert all('/../' not in f'/{path}' for path in paths)
    assert all('?' not in path and ':' not in path for path in paths)

    relations = next(file for file in payload['files'] if file['path'] == 'Relations.md')['content']
    assert '林/砚?' in relations
    assert '林:砚' in relations

    foreshadow = next(file for file in payload['files'] if file['path'] == 'Foreshadows/裂纹-玉佩.md')['content']
    assert '林/砚?' in foreshadow
    assert '[[Characters/林-砚]]' in foreshadow
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py::test_export_markdown_sanitizes_and_deduplicates_markdown_paths -v
```

Expected: FAIL because current slugging does not de-duplicate file paths, archive filename is missing, and relation/foreshadow Markdown does not resolve character names/links.

- [ ] **Step 3: Implement safe path map and richer render context**

Update `backend/app/snapshot_export/service.py` so `render_markdown_bundle(payload)`:

- builds character path map `{character_id: 'Characters/<safe>.md'}`;
- builds foreshadow path map `{foreshadow_id: 'Foreshadows/<safe>.md'}`;
- uses a `_unique_path(directory, stem, used_paths)` helper;
- uses character names/links in relations and foreshadow files;
- creates archive filename from sanitized world title.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py::test_export_markdown_sanitizes_and_deduplicates_markdown_paths -v
```

Expected: PASS.

## Task 3: Frontend API and download UI

**Files:**
- Modify: `frontend/src/api/client.test.ts`
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/world/WorldArchivePanel.test.tsx`
- Modify: `frontend/src/world/WorldArchivePanel.tsx`

- [ ] **Step 1: Write failing frontend API test**

In `frontend/src/api/client.test.ts`, import `exportWorldArchiveMarkdown` and add a test that calls it and asserts:

```ts
expect(fetchMock).toHaveBeenCalledWith(
  'http://localhost:8000/worlds/7/export/markdown',
  expect.objectContaining({ method: 'POST', body: '{}' }),
);
```

- [ ] **Step 2: Run API test to verify RED if helper is not covered**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: PASS if the helper already exists; this is acceptable because MVP13 found existing partial implementation. Continue with UI RED test for new behavior.

- [ ] **Step 3: Write failing UI download test**

In `frontend/src/world/WorldArchivePanel.test.tsx`, extend `markdownExport` with:

```ts
archive_filename: 'WorldSim-青岚城-v3-markdown.zip',
archive_base64: 'emlwLWRhdGE=',
```

Add a test that stubs `URL.createObjectURL` / `URL.revokeObjectURL`, clicks `导出世界档案`, then asserts:

```ts
expect(await screen.findByText('Archive：WorldSim-青岚城-v3-markdown.zip')).toBeInTheDocument();
expect(screen.getByRole('button', { name: '下载 Markdown ZIP' })).toBeInTheDocument();
expect(URL.createObjectURL).toHaveBeenCalled();
```

Expected before implementation: FAIL because filename and download button are not rendered.

- [ ] **Step 4: Update frontend types**

In `frontend/src/api/types.ts`, update `WorldMarkdownExportResponse`:

```ts
export type WorldMarkdownExportResponse = {
  world_id: number;
  world_version: number;
  generated_at: string;
  archive_filename: string;
  archive_base64: string;
  files: MarkdownExportFile[];
};
```

- [ ] **Step 5: Implement `WorldArchivePanel` download behavior**

In `frontend/src/world/WorldArchivePanel.tsx`:

- convert `archive_base64` to bytes;
- create a `Blob` with `application/zip`;
- create and store an object URL;
- render filename and a `下载 Markdown ZIP` link/button;
- revoke old object URLs when replaced.

- [ ] **Step 6: Run frontend targeted tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldArchivePanel.test.tsx src/world/WorldPage.test.tsx
```

Expected: PASS.

## Task 4: Full targeted verification, commit, and merge

**Files:**
- All modified files from Tasks 1-3.

- [ ] **Step 1: Create feature branch before implementation if not already on it**

Run:

```bash
git switch -c feat/mvp13-markdown-export
```

Expected: branch created from current `main` with uncommitted spec/plan changes carried over.

- [ ] **Step 2: Run backend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py tests/test_narrative_approval.py -v
```

Expected: PASS.

- [ ] **Step 3: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldArchivePanel.test.tsx src/world/WorldPage.test.tsx
```

Expected: PASS.

- [ ] **Step 4: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 5: Inline self-review**

Check:

- no Workflow/subagent/code-review subagent used;
- export endpoint remains auth/ownership protected;
- export remains read-only;
- reviewing/rejected drafts are excluded;
- generated ZIP contains exactly returned Markdown files;
- file paths are sanitized and de-duplicated;
- frontend download behavior does not require new dependencies.

- [ ] **Step 6: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-mvp13-markdown-export-design.md docs/superpowers/plans/2026-05-31-mvp13-markdown-export.md backend/app/snapshot_export/schemas.py backend/app/snapshot_export/service.py backend/tests/test_snapshot_export.py frontend/src/api/types.ts frontend/src/api/client.test.ts frontend/src/world/WorldArchivePanel.tsx frontend/src/world/WorldArchivePanel.test.tsx
git commit -m "feat: add downloadable markdown export bundle" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 7: Merge back to main without pushing**

Run:

```bash
git switch main
git merge feat/mvp13-markdown-export
```

- [ ] **Step 8: Post-merge verification**

Run the same backend targeted tests, frontend targeted tests, and frontend build again on `main`.

Expected: all pass.

- [ ] **Step 9: Final status**

Run:

```bash
git status --short --branch
```

Expected: `main...origin/main [领先 9]` and clean worktree. Do not push.

## Plan self-review

- Spec coverage: backend bundle contract, file structure, sanitization, approved-only rule, frontend download, tests, commit/merge/no-push are covered.
- Placeholder scan: no TBD/TODO placeholders are present.
- Type consistency: backend and frontend response fields use `archive_filename`, `archive_base64`, and `files` consistently.
- Scope: single subsystem extension around existing snapshot/export module and Archive panel; no decomposition needed.
