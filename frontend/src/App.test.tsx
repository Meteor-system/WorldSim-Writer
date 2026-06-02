import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { WorldOverview } from './api/types';
import { App } from './App';

const testWorld: WorldOverview = {
  id: 7,
  title: '青岚城',
  genre_template: 'xianxia',
  truth_canon: '灵脉正在衰退。',
  truth_canon_version: 1,
  world_version: 2,
  status: 'running',
  tone_profile: {},
  current_characters: [],
  current_foreshadows: [],
  current_relations: [],
  characters: [],
  relations: [],
  foreshadows: [],
  recent_events: [],
  story_arc: [],
  approved_chapter_count: 1,
};

vi.mock('./auth/AuthPage', () => ({
  AuthPage: ({ onAuth }: { onAuth: (email: string) => void }) => (
    <button type="button" onClick={() => onAuth('writer@example.com')}>登录测试用户</button>
  ),
}));

vi.mock('./world/WorldPage', () => ({
  WorldPage: ({ onEnterStudio }: { onEnterStudio: (world: WorldOverview) => void }) => (
    <button type="button" onClick={() => onEnterStudio(testWorld)}>进入测试创作台</button>
  ),
}));

vi.mock('./studio/StudioPage', () => ({
  StudioPage: ({ onApproved }: { onApproved: (world: WorldOverview) => void }) => (
    <button type="button" onClick={() => onApproved({ ...testWorld, world_version: 3 })}>写入测试正史</button>
  ),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
});

beforeEach(() => {
  localStorage.setItem('worldsim_token', 'token');
});

describe('App shell layout polish', () => {
  it('uses a motion app shell and reports approved world progress in Chinese version language', async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByTestId('app-shell')).toHaveClass('motion-page-enter');
    await user.click(screen.getByRole('button', { name: '进入测试创作台' }));
    await user.click(screen.getByRole('button', { name: '写入测试正史' }));

    expect(screen.getByRole('status')).toHaveTextContent('章节已通过，世界进度更新为第 3 版');
    expect(screen.getByRole('status')).not.toHaveTextContent('世界版本更新为 3');
  });
});
