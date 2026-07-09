import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { WorldSeedSummary } from '../api/types';
import { SeedLibraryPanel } from './SeedLibraryPanel';

const seeds: WorldSeedSummary[] = [
  {
    key: 'forgotten-sun-city',
    label: '无日城',
    genre_template: 'weird_fantasy',
    hook: '一座所有人都忘记太阳存在过的城市。',
    tension_profile: ['集体失忆', '禁忌天象'],
    starter_summary: {
      character_count: 2,
      relation_count: 1,
      foreshadow_count: 1,
      character_names: ['沈昼', '陆鸦'],
      foreshadow_titles: ['空白日晷'],
    },
    starter_guidance: {
      first_chapter_goal: '确认空白日晷为何没有影子。',
      protagonist_relationships: ['沈昼与陆鸦围绕太阳禁忌互相试探。'],
      foreshadow_pressure: ['空白日晷需要在开篇建立危险感。'],
      story_health_hints: ['确认前不写入正史，只作为开篇参考。'],
    },
  },
];

afterEach(() => cleanup());

describe('SeedLibraryPanel', () => {
  it('renders seed cards and calls apply/create callbacks', async () => {
    const user = userEvent.setup();
    const onApplySeed = vi.fn();
    const onCreateSeed = vi.fn();
    render(
      <SeedLibraryPanel
        seeds={seeds}
        selectedSeedKey="forgotten-sun-city"
        loading={false}
        error=""
        onApplySeed={onApplySeed}
        onCreateSeed={onCreateSeed}
      />,
    );

    expect(screen.getByText('灵感模板库')).toBeInTheDocument();
    expect(screen.getByText('无日城')).toBeInTheDocument();
    expect(screen.getByText('一座所有人都忘记太阳存在过的城市。')).toBeInTheDocument();
    expect(screen.getByText('集体失忆')).toBeInTheDocument();
    expect(screen.getByText('角色 2 · 关系 1 · 伏笔 1')).toBeInTheDocument();
    expect(screen.getByText('角色：沈昼、陆鸦')).toBeInTheDocument();
    expect(screen.getByText('首章目标：确认空白日晷为何没有影子。')).toBeInTheDocument();
    expect(screen.getByText(/故事健康：确认前不写入正史，只作为开篇参考。/)).toBeInTheDocument();
    expect(screen.getByText('当前套用中')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '套用到表单' }));
    await user.click(screen.getByRole('button', { name: '直接创建此模板' }));

    expect(onApplySeed).toHaveBeenCalledWith('forgotten-sun-city');
    expect(onCreateSeed).toHaveBeenCalledWith('forgotten-sun-city');
  });

  it('renders loading, error, and empty states', () => {
    const { rerender } = render(<SeedLibraryPanel seeds={[]} selectedSeedKey={null} loading error="" onApplySeed={vi.fn()} onCreateSeed={vi.fn()} />);
    expect(screen.getByRole('status')).toHaveTextContent('正在读取灵感模板库...');

    rerender(<SeedLibraryPanel seeds={[]} selectedSeedKey={null} loading={false} error="seed down" onApplySeed={vi.fn()} onCreateSeed={vi.fn()} />);
    expect(screen.getByRole('alert')).toHaveTextContent('seed down');

    rerender(<SeedLibraryPanel seeds={[]} selectedSeedKey={null} loading={false} error="" onApplySeed={vi.fn()} onCreateSeed={vi.fn()} />);
    expect(screen.getByText('暂无可用灵感模板。')).toBeInTheDocument();
  });
});
