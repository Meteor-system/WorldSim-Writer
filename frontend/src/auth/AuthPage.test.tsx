import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthPage } from './AuthPage';
import { apiRequest } from '../api/client';

vi.mock('../api/client', () => ({ apiRequest: vi.fn() }));

afterEach(() => cleanup());

beforeEach(() => {
  vi.mocked(apiRequest).mockReset();
  localStorage.clear();
});

describe('AuthPage layout polish', () => {
  it('renders a layered Chinese entry page with responsive actions and motion classes', () => {
    render(<AuthPage onAuth={vi.fn()} />);

    expect(screen.getByText('故事世界运营台')).toBeInTheDocument();
    expect(screen.getByText('登录后创建世界胚胎、推进章节草稿，并把通过审核的章节写入正史。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('WorldSim Archive');

    const panel = screen.getByTestId('auth-entry-panel');
    expect(panel).toHaveClass('motion-page-enter');
    expect(panel).toHaveClass('surface-layer');

    const actions = screen.getByTestId('auth-actions');
    expect(actions).toHaveClass('flex-wrap');
    expect(actions).toHaveClass('gap-3');
  });
});

describe('AuthPage validation and loading', () => {
  it('marks email as type=email and required, password as required', () => {
    render(<AuthPage onAuth={vi.fn()} />);
    const email = screen.getByLabelText('邮箱') as HTMLInputElement;
    const password = screen.getByLabelText('密码') as HTMLInputElement;
    expect(email).toHaveAttribute('type', 'email');
    expect(email).toBeRequired();
    expect(password).toBeRequired();
  });

  it('blocks submit and shows an error when email is empty', async () => {
    const user = userEvent.setup();
    render(<AuthPage onAuth={vi.fn()} />);
    await user.clear(screen.getByLabelText('邮箱'));
    await user.click(screen.getByRole('button', { name: '登录' }));
    expect(await screen.findByText('请输入邮箱')).toBeInTheDocument();
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('blocks submit and shows an error for malformed email', async () => {
    const user = userEvent.setup();
    render(<AuthPage onAuth={vi.fn()} />);
    const email = screen.getByLabelText('邮箱');
    await user.clear(email);
    await user.type(email, 'not-an-email');
    await user.click(screen.getByRole('button', { name: '登录' }));
    expect(await screen.findByText('邮箱格式不正确')).toBeInTheDocument();
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('blocks register submit when password is shorter than 8 chars', async () => {
    const user = userEvent.setup();
    render(<AuthPage onAuth={vi.fn()} />);
    const password = screen.getByLabelText('密码');
    await user.clear(password);
    await user.type(password, 'short');
    await user.click(screen.getByRole('button', { name: '注册' }));
    expect(await screen.findByText('注册密码至少 8 位')).toBeInTheDocument();
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('shows loading text and disables both buttons while submitting', async () => {
    const user = userEvent.setup();
    let resolveAuth: (value: unknown) => void = () => {};
    vi.mocked(apiRequest).mockImplementation(
      () => new Promise((resolve) => { resolveAuth = resolve; }),
    );
    render(<AuthPage onAuth={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: '登录' }));
    expect(await screen.findByRole('button', { name: '登录中…' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '注册中…' })).toBeDisabled();

    resolveAuth({ access_token: 't', token_type: 'bearer', user: { email: 'writer@example.com' } });
    await waitFor(() => expect(screen.queryByRole('button', { name: '登录中…' })).not.toBeInTheDocument());
  });
});
