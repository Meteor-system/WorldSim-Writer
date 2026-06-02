import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthPage } from './AuthPage';

vi.mock('../api/client', () => ({ apiRequest: vi.fn() }));

afterEach(() => cleanup());

describe('AuthPage layout polish', () => {
  it('renders a layered Chinese entry page with responsive actions and motion classes', () => {
    render(<AuthPage onAuth={vi.fn()} />);

    expect(screen.getByText('进入故事世界运营台')).toBeInTheDocument();
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
