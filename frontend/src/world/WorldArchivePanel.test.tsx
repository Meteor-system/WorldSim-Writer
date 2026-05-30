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
  files: [
    { path: 'World.md', content: '# World' },
    { path: 'Timeline/Events.md', content: '# Timeline' },
  ],
};

afterEach(() => cleanup());

describe('WorldArchivePanel', () => {
  it('renders archive controls', () => {
    render(<WorldArchivePanel onCreateSnapshot={vi.fn()} onExportMarkdown={vi.fn()} />);

    expect(screen.getByText('World Archive')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建世界快照' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '导出世界档案' })).toBeInTheDocument();
  });

  it('shows snapshot success state', async () => {
    const user = userEvent.setup();
    const onCreateSnapshot = vi.fn(async () => snapshot);

    render(<WorldArchivePanel onCreateSnapshot={onCreateSnapshot} onExportMarkdown={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: '创建世界快照' }));

    expect(onCreateSnapshot).toHaveBeenCalledOnce();
    expect(await screen.findByText('快照已创建：版本 3')).toBeInTheDocument();
    expect(screen.getByText('Snapshot #12')).toBeInTheDocument();
  });

  it('shows snapshot error state', async () => {
    const user = userEvent.setup();
    const onCreateSnapshot = vi.fn(async () => {
      throw new Error('boom');
    });

    render(<WorldArchivePanel onCreateSnapshot={onCreateSnapshot} onExportMarkdown={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: '创建世界快照' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('创建快照失败');
  });

  it('shows export success state with generated files', async () => {
    const user = userEvent.setup();
    const onExportMarkdown = vi.fn(async () => markdownExport);

    render(<WorldArchivePanel onCreateSnapshot={vi.fn()} onExportMarkdown={onExportMarkdown} />);

    await user.click(screen.getByRole('button', { name: '导出世界档案' }));

    expect(onExportMarkdown).toHaveBeenCalledOnce();
    expect(await screen.findByText('导出成功：2 个 Markdown 文件已生成')).toBeInTheDocument();
    expect(screen.getByText('World.md')).toBeInTheDocument();
    expect(screen.getByText('Timeline/Events.md')).toBeInTheDocument();
  });

  it('shows export error state', async () => {
    const user = userEvent.setup();
    const onExportMarkdown = vi.fn(async () => {
      throw new Error('boom');
    });

    render(<WorldArchivePanel onCreateSnapshot={vi.fn()} onExportMarkdown={onExportMarkdown} />);

    await user.click(screen.getByRole('button', { name: '导出世界档案' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('导出世界档案失败');
  });
});
