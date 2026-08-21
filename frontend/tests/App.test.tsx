import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AUTH_EXPIRED_EVENT, AUTH_TOKEN_KEY } from '../src/api/client';
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

vi.mock('../src/workbench/WorkbenchTopBar', () => ({
  WorkbenchTopBar: ({ onLogout }: { onLogout: () => void }) => (
    <button onClick={onLogout}>退出登录</button>
  ),
}));

vi.mock('../src/workbench/WorkbenchBookshelf', () => ({
  WorkbenchBookshelf: ({
    onOpenWorld,
    refreshKey,
  }: {
    onOpenWorld: (world: { id: number }) => void;
    refreshKey?: { worldId: number; token: number } | null;
  }) => (
    <section>
      <button onClick={() => onOpenWorld({ id: 7 })}>进入测试 Studio</button>
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

  it('returns from the authenticated bookshelf or Studio to AuthPage on an authentication expiration event', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'fake-token');
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole('button', { name: '进入测试 Studio' }));
    window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));

    expect(await screen.findByText('登录')).toBeInTheDocument();
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull();
    expect(screen.queryByRole('button', { name: '退出登录' })).not.toBeInTheDocument();
  });

  it('does not leave the authenticated view for a non-authentication event', () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'fake-token');
    render(<App />);

    window.dispatchEvent(new CustomEvent('worldsim:request-failed'));

    expect(screen.getByRole('button', { name: '进入测试 Studio' })).toBeInTheDocument();
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe('fake-token');
  });

  it('manually logs out and clears authenticated UI state', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'fake-token');
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole('button', { name: '退出登录' }));

    expect(await screen.findByText('登录')).toBeInTheDocument();
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull();
  });

  it('removes the expiration listener when unmounted', () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'fake-token');
    const { unmount } = render(<App />);

    unmount();
    window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));

    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe('fake-token');
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
