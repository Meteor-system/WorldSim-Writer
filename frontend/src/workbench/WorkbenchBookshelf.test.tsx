import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiRequest } from '../api/client';
import { WorkbenchBookshelf } from './WorkbenchBookshelf';

vi.mock('../api/client', () => ({
  apiRequest: vi.fn(),
  updateWorldStatus: vi.fn(async () => ({ id: 3, status: 'active' })),
}));

afterEach(() => {
  cleanup();
});

const worldList = [
  { id: 1, title: '活跃小说', genre_template: 'zombie_apocalypse', world_version: 4, status: 'active' },
  { id: 2, title: '归档小说', genre_template: 'xianxia_intrigue', world_version: 2, status: 'archived' },
];

describe('WorkbenchBookshelf', () => {
  it('lists active and archived worlds and opens one through the overview', async () => {
    vi.mocked(apiRequest).mockImplementation(async (path: string) => {
      if (path === '/worlds') return worldList;
      if (path === '/worlds/1/overview') return { id: 1, title: '活跃小说', world_version: 4, status: 'active' };
      throw new Error('unexpected path');
    });
    const user = userEvent.setup();
    const onOpenWorld = vi.fn();
    render(<WorkbenchBookshelf onCreateWorld={vi.fn()} onOpenWorld={onOpenWorld} />);

    expect(await screen.findByText('活跃小说')).toBeInTheDocument();
    expect(screen.getByText('归档小说')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '打开 活跃小说' }));
    expect(onOpenWorld).toHaveBeenCalledWith(expect.objectContaining({ id: 1, title: '活跃小说' }));
  });

  it('shows the empty state and asks the user to create a world', async () => {
    vi.mocked(apiRequest).mockImplementation(async () => []);
    const user = userEvent.setup();
    const onCreateWorld = vi.fn();
    render(<WorkbenchBookshelf onCreateWorld={onCreateWorld} onOpenWorld={vi.fn()} />);

    expect(await screen.findByText(/暂无活跃小说/)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '新建世界' }));
    expect(onCreateWorld).toHaveBeenCalledTimes(1);
  });
});
