import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { WorldSearchResponse } from '../api/types';
import { WorldSearchPanel } from './WorldSearchPanel';

const searchResponse: WorldSearchResponse = {
  world_id: 7,
  query: '灯塔',
  object_type_counts: { character: 1, foreshadow: 1 },
  results: [
    {
      object_type: 'character',
      object_id: 1,
      title: '许砚',
      subtitle: 'Character · protagonist',
      snippet: '灯塔维修工程师正在查明黑匣子脉冲来源。',
      metadata: { status: 'active' },
    },
    {
      object_type: 'foreshadow',
      object_id: 2,
      title: '黑匣子脉冲',
      subtitle: 'Foreshadow · planted · urgency 4',
      snippet: '废弃黑匣子收到来自未来的求救信号。',
      metadata: { status: 'planted' },
    },
  ],
};

afterEach(() => cleanup());

describe('WorldSearchPanel', () => {
  it('renders search results with counts and snippets', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn().mockResolvedValue(searchResponse);
    render(<WorldSearchPanel worldId={7} onSearch={onSearch} />);

    expect(screen.getByText('Global Search')).toBeInTheDocument();
    await user.type(screen.getByLabelText('搜索世界资料'), '灯塔');
    await user.click(screen.getByRole('button', { name: '搜索' }));

    await waitFor(() => expect(onSearch).toHaveBeenCalledWith(7, { q: '灯塔', object_types: [], limit: 20 }));
    expect(await screen.findByText('找到 2 条结果')).toBeInTheDocument();
    expect(screen.getByText('character × 1')).toBeInTheDocument();
    expect(screen.getByText('foreshadow × 1')).toBeInTheDocument();
    expect(screen.getByText('许砚')).toBeInTheDocument();
    expect(screen.getByText('废弃黑匣子收到来自未来的求救信号。')).toBeInTheDocument();
  });

  it('sends selected object type filters', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn().mockResolvedValue(searchResponse);
    render(<WorldSearchPanel worldId={7} onSearch={onSearch} />);

    await user.type(screen.getByLabelText('搜索世界资料'), '灯塔');
    await user.click(screen.getByRole('button', { name: '角色' }));
    await user.click(screen.getByRole('button', { name: '搜索' }));

    await waitFor(() => expect(onSearch).toHaveBeenCalledWith(7, { q: '灯塔', object_types: ['character'], limit: 20 }));
  });

  it('does not search blank queries', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn().mockResolvedValue(searchResponse);
    render(<WorldSearchPanel worldId={7} onSearch={onSearch} />);

    await user.click(screen.getByRole('button', { name: '搜索' }));

    expect(onSearch).not.toHaveBeenCalled();
    expect(screen.getByText('请输入关键词后再搜索。')).toBeInTheDocument();
  });

  it('shows localized API errors', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn().mockRejectedValue(new Error('search down'));
    render(<WorldSearchPanel worldId={7} onSearch={onSearch} />);

    await user.type(screen.getByLabelText('搜索世界资料'), '灯塔');
    await user.click(screen.getByRole('button', { name: '搜索' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('search down');
  });
});
