import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { WorldArchivePanel } from './WorldArchivePanel';

const snapshot = {
  id: 12,
  world_id: 7,
  world_version: 3,
  label: null,
  note: null,
  created_at: '2026-05-30T00:00:00Z',
};

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

const snapshots = [
  { ...snapshot, id: 12, world_version: 2, label: 'Before reveal' },
  { ...snapshot, id: 13, world_version: 3, label: 'After reveal' },
];

const compareResponse = {
  world_id: 7,
  base_snapshot: snapshots[0],
  target_snapshot: snapshots[1],
  summary: { total_changes: 2, object_type_counts: { character: 1, foreshadow: 1 } },
  changes: {
    world: [],
    characters: [
      {
        object_type: 'character',
        object_id: 1,
        change_type: 'changed' as const,
        title: '林砚',
        fields_changed: ['status'],
        before: { status: '调查湿信' },
        after: { status: '追查档案门廊' },
      },
    ],
    relations: [],
    foreshadows: [
      {
        object_type: 'foreshadow',
        object_id: 9,
        change_type: 'added' as const,
        title: '雨巷铜铃',
        fields_changed: [],
        before: null,
        after: { title: '雨巷铜铃' },
      },
    ],
    chapters: [],
    events: [],
  },
};

function renderArchivePanel(overrides = {}) {
  return render(
    <WorldArchivePanel
      onCreateSnapshot={vi.fn()}
      onExportMarkdown={vi.fn()}
      onListSnapshots={vi.fn(async () => ({ world_id: 7, snapshots }))}
      onCompareSnapshots={vi.fn(async () => compareResponse)}
      {...overrides}
    />,
  );
}

afterEach(() => cleanup());

describe('WorldArchivePanel', () => {
  it('renders archive controls', () => {
    renderArchivePanel();

    expect(screen.getByText('世界档案库')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建世界快照' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '导出世界档案' })).toBeInTheDocument();
    expect(screen.getByText('点击导出后会生成可下载 ZIP，并在下方显示内联 Markdown 预览；不会写入服务器文件系统。')).toBeInTheDocument();
  });

  it('shows snapshot success state', async () => {
    const user = userEvent.setup();
    const onCreateSnapshot = vi.fn(async () => snapshot);

    renderArchivePanel({ onCreateSnapshot });

    await user.click(screen.getByRole('button', { name: '创建世界快照' }));

    expect(onCreateSnapshot).toHaveBeenCalledOnce();
    expect(await screen.findByText('保存点已创建：第 3 版')).toBeInTheDocument();
    expect(screen.getByText('可在快照对比中作为回看基准。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('Snapshot #12');
  });

  it('keeps archived archive tools read-only while preserving export and snapshot history', () => {
    const onCreateSnapshot = vi.fn(async () => snapshot);

    renderArchivePanel({ readOnly: true, onCreateSnapshot });

    expect(screen.getByText('已归档小说为只读模式；可继续导出档案和查看历史快照，恢复写作后才能创建新快照。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '创建世界快照' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '导出世界档案' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '加载快照列表' })).toBeInTheDocument();
    expect(onCreateSnapshot).not.toHaveBeenCalled();
  });

  it('shows snapshot error state', async () => {
    const user = userEvent.setup();
    const onCreateSnapshot = vi.fn(async () => {
      throw new Error('boom');
    });

    renderArchivePanel({ onCreateSnapshot });

    await user.click(screen.getByRole('button', { name: '创建世界快照' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('创建快照失败');
  });

  it('shows export success state with archive metadata, generated files, and download action', async () => {
    const user = userEvent.setup();
    const onExportMarkdown = vi.fn(async () => markdownExport);
    const createObjectURL = vi.fn(() => 'blob:markdown-zip');
    const revokeObjectURL = vi.fn();
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL });

    renderArchivePanel({ onExportMarkdown });

    await user.click(screen.getByRole('button', { name: '导出世界档案' }));

    expect(onExportMarkdown).toHaveBeenCalledOnce();
    expect(await screen.findByText('Obsidian ZIP 已准备好')).toBeInTheDocument();
    expect(screen.getByText('下载文件：WorldSim-青岚城-v3-markdown.zip')).toBeInTheDocument();
    expect(screen.getByText('世界进度：第 3 版 · Markdown 文件：2 个')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('格式：zip');
    expect(document.body).not.toHaveTextContent('编码：base64');
    expect(document.body).not.toHaveTextContent('内联预览');
    expect(screen.getByText('生成时间：2026-05-30T00:00:00Z')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '下载 Markdown ZIP' })).toHaveAttribute('href', 'blob:markdown-zip');
    expect(screen.getByRole('link', { name: '下载 Markdown ZIP' })).toHaveAttribute('download', 'WorldSim-青岚城-v3-markdown.zip');
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(screen.getAllByText('World.md').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Timeline.md').length).toBeGreaterThan(0);
  });

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

  it('shows export error state', async () => {
    const user = userEvent.setup();
    const onExportMarkdown = vi.fn(async () => {
      throw new Error('boom');
    });

    renderArchivePanel({ onExportMarkdown });

    await user.click(screen.getByRole('button', { name: '导出世界档案' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('导出世界档案失败');
  });

  it('loads snapshots, compares two selected snapshots, and renders diff results', async () => {
    const user = userEvent.setup();
    const onListSnapshots = vi.fn(async () => ({ world_id: 7, snapshots }));
    const onCompareSnapshots = vi.fn(async () => compareResponse);

    renderArchivePanel({ onListSnapshots, onCompareSnapshots });

    expect(screen.getByText('快照对比')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '对比快照' })).toBeDisabled();

    await user.click(screen.getByRole('button', { name: '加载快照列表' }));
    await user.selectOptions(await screen.findByLabelText('基准快照'), '12');
    await user.selectOptions(screen.getByLabelText('目标快照'), '13');
    await user.click(screen.getByRole('button', { name: '对比快照' }));

    expect(onListSnapshots).toHaveBeenCalledOnce();
    expect(onCompareSnapshots).toHaveBeenCalledWith(12, 13);
    expect(await screen.findByText('总变更：2')).toBeInTheDocument();
    expect(screen.getByText('角色：1')).toBeInTheDocument();
    expect(screen.getByText('林砚')).toBeInTheDocument();
    expect(document.body).toHaveTextContent('角色 · 变化：资料已更新');
    expect(document.body).toHaveTextContent('调整项：状态');
    expect(document.body).not.toHaveTextContent('character：1');
    expect(document.body).not.toHaveTextContent('字段：status');
    expect(screen.getByText('雨巷铜铃')).toBeInTheDocument();
  });

  it('shows snapshot compare error state', async () => {
    const user = userEvent.setup();
    const onListSnapshots = vi.fn(async () => ({ world_id: 7, snapshots }));
    const onCompareSnapshots = vi.fn(async () => {
      throw new Error('boom');
    });

    renderArchivePanel({ onListSnapshots, onCompareSnapshots });

    await user.click(screen.getByRole('button', { name: '加载快照列表' }));
    await user.selectOptions(await screen.findByLabelText('基准快照'), '12');
    await user.selectOptions(screen.getByLabelText('目标快照'), '13');
    await user.click(screen.getByRole('button', { name: '对比快照' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('对比快照失败');
  });
});
