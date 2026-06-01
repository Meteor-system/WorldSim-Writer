# MVP42 Export Download Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the existing Markdown archive export so users can clearly download the ZIP and preview inline Markdown files from the World Archive panel.

**Architecture:** This is a frontend-only enhancement. The backend `POST /worlds/{world_id}/export/markdown` JSON contract remains unchanged; the frontend aligns its TypeScript type with the hardened response and renders a clearer export-ready UI using the existing `archive_base64` and `files` fields.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## File structure

- Modify: `frontend/src/api/types.ts`
  - Add `archive_format`, `archive_encoding`, and `files_are_inline` to `WorldMarkdownExportResponse`.
- Modify: `frontend/src/world/WorldArchivePanel.tsx`
  - Track selected inline Markdown file path.
  - Display archive metadata and download-ready copy.
  - Render a file selector and preformatted Markdown preview.
- Modify: `frontend/src/world/WorldArchivePanel.test.tsx`
  - Extend the export mock with the hardened metadata fields.
  - Add RED/GREEN tests for metadata display and file preview switching.
- No backend production files are changed.

---

### Task 1: Align export response type and show archive metadata

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/world/WorldArchivePanel.test.tsx`
- Modify: `frontend/src/world/WorldArchivePanel.tsx`

- [ ] **Step 1: Write the failing test**

In `frontend/src/world/WorldArchivePanel.test.tsx`, update the `markdownExport` fixture so it matches the hardened backend response:

```ts
const markdownExport = {
  world_id: 7,
  world_version: 3,
  generated_at: '2026-05-30T00:00:00Z',
  archive_filename: 'WorldSim-青岚城-v3-markdown.zip',
  archive_format: 'zip',
  archive_encoding: 'base64',
  archive_base64: 'emlwLWRhdGE=',
  files_are_inline: true,
  files: [
    { path: 'World.md', content: '# World' },
    { path: 'Timeline.md', content: '# Timeline' },
  ],
};
```

Then replace the export success test with expectations for explicit metadata:

```ts
it('shows export success state with archive metadata, generated files, and download action', async () => {
  const user = userEvent.setup();
  const onExportMarkdown = vi.fn(async () => markdownExport);
  const createObjectURL = vi.fn(() => 'blob:markdown-zip');
  const revokeObjectURL = vi.fn();
  vi.stubGlobal('URL', { createObjectURL, revokeObjectURL });

  renderArchivePanel({ onExportMarkdown });

  await user.click(screen.getByRole('button', { name: '导出世界档案' }));

  expect(onExportMarkdown).toHaveBeenCalledOnce();
  expect(await screen.findByText('下载包已就绪')).toBeInTheDocument();
  expect(screen.getByText('Archive：WorldSim-青岚城-v3-markdown.zip')).toBeInTheDocument();
  expect(screen.getByText('格式：zip · 编码：base64 · 内联预览：是')).toBeInTheDocument();
  expect(screen.getByText('世界版本：v3 · 文件数：2')).toBeInTheDocument();
  expect(screen.getByText('生成时间：2026-05-30T00:00:00Z')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '下载 Markdown ZIP' })).toHaveAttribute('href', 'blob:markdown-zip');
  expect(screen.getByRole('link', { name: '下载 Markdown ZIP' })).toHaveAttribute('download', 'WorldSim-青岚城-v3-markdown.zip');
  expect(createObjectURL).toHaveBeenCalledOnce();
  expect(screen.getByText('World.md')).toBeInTheDocument();
  expect(screen.getByText('Timeline.md')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
```

Expected: FAIL because `下载包已就绪` and the new archive metadata text are not rendered yet.

- [ ] **Step 3: Update the TypeScript response type**

In `frontend/src/api/types.ts`, change `WorldMarkdownExportResponse` to:

```ts
export type WorldMarkdownExportResponse = {
  world_id: number;
  world_version: number;
  generated_at: string;
  archive_filename: string;
  archive_format: string;
  archive_encoding: string;
  archive_base64: string;
  files_are_inline: boolean;
  files: MarkdownExportFile[];
};
```

- [ ] **Step 4: Render minimal archive metadata**

In `frontend/src/world/WorldArchivePanel.tsx`, replace the current export success block inside the Markdown export card with this structure while preserving the existing button and error state:

```tsx
{markdownExport && (
  <div className="mt-2 text-sm">
    <p className="font-black text-[#3b2511]">下载包已就绪</p>
    <p className="manuscript mt-1">导出成功：{markdownExport.files.length} 个 Markdown 文件已生成</p>
    <p className="mt-1 font-bold text-[#5e3b1c]">Archive：{markdownExport.archive_filename}</p>
    <p className="manuscript mt-1 text-sm">格式：{markdownExport.archive_format} · 编码：{markdownExport.archive_encoding} · 内联预览：{markdownExport.files_are_inline ? '是' : '否'}</p>
    <p className="manuscript mt-1 text-sm">世界版本：v{markdownExport.world_version} · 文件数：{markdownExport.files.length}</p>
    <p className="manuscript mt-1 text-sm">生成时间：{markdownExport.generated_at}</p>
    {downloadUrl && (
      <a className="secondary-button mt-3 inline-flex" href={downloadUrl} download={markdownExport.archive_filename}>
        下载 Markdown ZIP
      </a>
    )}
    <ul className="mt-2 space-y-1 ink-muted">
      {markdownExport.files.map((file) => (
        <li key={file.path}>{file.path}</li>
      ))}
    </ul>
  </div>
)}
```

- [ ] **Step 5: Run the test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
```

Expected: PASS for the updated export metadata expectations.

---

### Task 2: Add inline Markdown file preview and switching

**Files:**
- Modify: `frontend/src/world/WorldArchivePanel.test.tsx`
- Modify: `frontend/src/world/WorldArchivePanel.tsx`

- [ ] **Step 1: Write the failing preview test**

Add this test to `frontend/src/world/WorldArchivePanel.test.tsx`:

```ts
it('previews the selected inline markdown file and switches between files', async () => {
  const user = userEvent.setup();
  const onExportMarkdown = vi.fn(async () => markdownExport);
  vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:markdown-zip'), revokeObjectURL: vi.fn() });

  renderArchivePanel({ onExportMarkdown });

  await user.click(screen.getByRole('button', { name: '导出世界档案' }));

  expect(await screen.findByText('Markdown 预览')).toBeInTheDocument();
  expect(screen.getByLabelText('选择预览文件')).toHaveValue('World.md');
  expect(screen.getByText('# World')).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText('选择预览文件'), 'Timeline.md');

  expect(screen.getByText('# Timeline')).toBeInTheDocument();
  expect(screen.queryByText('# World')).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
```

Expected: FAIL because `Markdown 预览` and the file selector do not exist yet.

- [ ] **Step 3: Add selected export path state**

In `frontend/src/world/WorldArchivePanel.tsx`, add state next to the export state:

```ts
const [selectedExportPath, setSelectedExportPath] = useState('');
```

In `handleExportMarkdown()`, after receiving `exported`, set the default selected file:

```ts
setSelectedExportPath(exported.files[0]?.path ?? '');
```

In the export failure branch, clear it:

```ts
setSelectedExportPath('');
```

- [ ] **Step 4: Derive selected preview file**

Near `const canCompare = ...`, add:

```ts
const selectedExportFile = markdownExport?.files.find((file) => file.path === selectedExportPath) ?? markdownExport?.files[0] ?? null;
```

- [ ] **Step 5: Render preview UI**

Inside the `markdownExport && (...)` block after the file list, add:

```tsx
{markdownExport.files_are_inline && markdownExport.files.length > 0 && selectedExportFile && (
  <div className="mt-4 rounded-2xl bg-white/50 p-3">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h4 className="font-black text-[#3b2511]">Markdown 预览</h4>
      <label className="text-sm font-bold text-[#5e3b1c]">
        选择预览文件
        <select
          className="paper-input mt-1"
          aria-label="选择预览文件"
          value={selectedExportFile.path}
          onChange={(event) => setSelectedExportPath(event.target.value)}
        >
          {markdownExport.files.map((file) => (
            <option key={file.path} value={file.path}>{file.path}</option>
          ))}
        </select>
      </label>
    </div>
    <pre className="manuscript mt-3 max-h-72 overflow-auto whitespace-pre-wrap rounded-xl bg-amber-50/70 p-3 text-sm">{selectedExportFile.content}</pre>
  </div>
)}
```

- [ ] **Step 6: Run the test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
```

Expected: PASS.

---

### Task 3: Clarify empty and failure states without changing backend behavior

**Files:**
- Modify: `frontend/src/world/WorldArchivePanel.test.tsx`
- Modify: `frontend/src/world/WorldArchivePanel.tsx`

- [ ] **Step 1: Write the failing empty-state expectation**

In `renders archive controls`, add:

```ts
expect(screen.getByText('点击导出后会生成可下载 ZIP，并在下方显示内联 Markdown 预览；不会写入服务器文件系统。')).toBeInTheDocument();
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
```

Expected: FAIL because the exact empty-state copy does not exist yet.

- [ ] **Step 3: Update the empty-state copy**

In `frontend/src/world/WorldArchivePanel.tsx`, replace the existing empty export copy:

```tsx
{!markdownExport && !exportError && <p className="ink-muted mt-2 text-sm">导出只返回文本，不写入服务器文件系统。</p>}
```

with:

```tsx
{!markdownExport && !exportError && <p className="ink-muted mt-2 text-sm">点击导出后会生成可下载 ZIP，并在下方显示内联 Markdown 预览；不会写入服务器文件系统。</p>}
```

- [ ] **Step 4: Run the test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
```

Expected: PASS.

---

### Task 4: Verification before commit

**Files:**
- Verify only unless failures require minimal fixes.

- [ ] **Step 1: Run targeted archive panel tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
```

Expected: all `WorldArchivePanel` tests pass.

- [ ] **Step 2: Run targeted API client tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: all API client tests pass.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 4: Optional backend safety check for export contract**

Run if backend environment is available:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 conda run -n worldsim pytest tests/test_snapshot_export.py::test_export_markdown_returns_downloadable_obsidian_zip_bundle -v
```

Expected: PASS. If the environment is unavailable, record that backend production code was not changed and frontend build/type checks covered the changed surface.

---

### Task 5: Commit and fast-forward merge to main

**Files:**
- Commit all MVP42 spec/plan/test/frontend changes.

- [ ] **Step 1: Check git status**

Run:

```bash
cd /opt/WorldSim-Writer && git status --short --branch
```

Expected: on `feat/mvp42-export-download` with only MVP42 files changed.

- [ ] **Step 2: Commit**

Run:

```bash
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-06-01-mvp42-export-download-design.md docs/superpowers/plans/2026-06-01-mvp42-export-download.md frontend/src/api/types.ts frontend/src/world/WorldArchivePanel.tsx frontend/src/world/WorldArchivePanel.test.tsx && git commit -m "feat: improve markdown export download UX"
```

Expected: commit succeeds.

- [ ] **Step 3: Fast-forward merge to main**

Run:

```bash
cd /opt/WorldSim-Writer && git checkout main && git merge --ff-only feat/mvp42-export-download
```

Expected: fast-forward merge succeeds.

- [ ] **Step 4: Post-merge verification**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: targeted archive tests and frontend build pass on `main`.

- [ ] **Step 5: Confirm no push**

Run:

```bash
cd /opt/WorldSim-Writer && git status --short --branch
```

Expected: on `main`, clean working tree, local branch ahead of remote if remote tracking exists. Do not run `git push`.

---

## Self-review

- Spec coverage: all MVP42 goals are covered by Tasks 1-3 and verified in Task 4.
- Placeholder scan: no TBD/TODO/fill-in placeholders remain.
- Type consistency: `WorldMarkdownExportResponse` fields match the hardened backend response and the test fixture.
- Scope check: no backend endpoint or archive-generation changes are included.

## Execution status — 2026-06-01

Completed on `feat/mvp42-export-download`:

- Task 1 RED: `WorldArchivePanel.test.tsx` failed because `下载包已就绪` and archive metadata were missing.
- Task 1 GREEN: added export metadata fields to the frontend type and rendered archive filename, ZIP/base64 metadata, world version, file count, generated timestamp, and download link.
- Task 2 RED: `WorldArchivePanel.test.tsx` failed because `Markdown 预览` and file selection did not exist.
- Task 2 GREEN: added `selectedExportPath`, default first-file selection, file selector, and plain text Markdown preview.
- Task 3 RED: `WorldArchivePanel.test.tsx` failed because the clearer empty-state copy did not exist.
- Task 3 GREEN: updated the empty state to explain ZIP download plus inline preview without server-side writes.
- Build surfaced one type fixture drift in `WorldPage.test.tsx`; updated that mock to include the hardened export metadata.

Pre-commit verification:

```text
cd /opt/WorldSim-Writer/frontend && npm run build
✓ built

cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx src/world/WorldPage.test.tsx src/api/client.test.ts
Test Files 3 passed (3)
Tests 33 passed (33)
```

Backend note: no backend production code changed. A conda-based optional backend export safety check could not run in this environment because the configured `worldsim` conda environment was unavailable; frontend type/build checks and existing hardened backend tests cover the changed surface.
