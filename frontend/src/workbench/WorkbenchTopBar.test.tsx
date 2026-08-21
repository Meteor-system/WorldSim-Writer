import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { apiRequest } from '../api/client';
import { WorkbenchTopBar } from './WorkbenchTopBar';

vi.mock('../api/client', () => ({
  apiRequest: vi.fn(async () => []),
  listWorldSeeds: vi.fn(async () => ({ seeds: [] })),
}));

describe('WorkbenchTopBar', () => {
  it('renders world switcher and opens the create world modal', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    render(
      <WorkbenchTopBar
        currentWorldId={7}
        currentWorldVersion={2}
        currentWorldStatus="active"
        onSwitchWorld={vi.fn()}
        onCreated={onCreated}
        onLogout={vi.fn()}
        userEmail="test@example.com"
      />,
    );

    expect(screen.getByLabelText('切换世界')).toBeInTheDocument();
    expect(screen.queryByRole('dialog', { name: '新建世界' })).toBeNull();
    await user.click(screen.getByRole('button', { name: '新建世界' }));
    expect(screen.getByRole('dialog', { name: '新建世界' })).toBeInTheDocument();
    expect(apiRequest).toHaveBeenCalledWith('/worlds');
    await user.click(screen.getByRole('button', { name: '关闭 ✕' }));
    expect(screen.queryByRole('dialog', { name: '新建世界' })).toBeNull();
  });
});
