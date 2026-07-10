import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/App';

vi.mock('../src/auth/AuthPage', () => ({
  AuthPage: () => (
    <section>
      <h1>WorldSim-Writer</h1>
      <button>登录</button>
      <button>注册</button>
    </section>
  ),
}));

vi.mock('../src/studio/StudioPage', () => ({
  StudioPage: ({ onAbandoned }: { onAbandoned?: (worldId: number) => void }) => (
    <button onClick={() => onAbandoned?.(7)}>完成放弃章节</button>
  ),
}));

vi.mock('../src/world/WorldPage', () => ({
  WorldPage: ({
    onEnterStudio,
    refreshKey,
  }: {
    onEnterStudio: (world: { id: number }) => void;
    refreshKey?: { worldId: number; token: number } | null;
  }) => (
    <section>
      <button onClick={() => onEnterStudio({ id: 7 })}>进入测试 Studio</button>
      <output data-testid="world-refresh-key">
        {refreshKey ? `${refreshKey.worldId}:${refreshKey.token}` : 'none'}
      </output>
    </section>
  ),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
});

describe('App', () => {
  it('shows the auth page when no token exists', () => {
    localStorage.clear();

    render(<App />);

    expect(screen.getByText('WorldSim-Writer')).toBeInTheDocument();
    expect(screen.getByText('登录')).toBeInTheDocument();
    expect(screen.getByText('注册')).toBeInTheDocument();
  });

  it('exits Studio and forwards an abandon refresh signal for the same world', async () => {
    localStorage.setItem('worldsim_token', 'test-token');
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByTestId('world-refresh-key')).toHaveTextContent('none');
    await user.click(screen.getByRole('button', { name: '进入测试 Studio' }));
    await user.click(screen.getByRole('button', { name: '完成放弃章节' }));

    expect(screen.getByRole('button', { name: '进入测试 Studio' })).toBeInTheDocument();
    expect(screen.getByTestId('world-refresh-key')).toHaveTextContent('7:1');
  });
});
