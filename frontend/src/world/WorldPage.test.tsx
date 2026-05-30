import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiRequest, getChapterHistory, getChapterHistoryDetail, getNextChapterPrep, getRelations } from '../api/client';
import type { WorldOverview } from '../api/types';
import { WorldPage } from './WorldPage';

vi.mock('../api/client', () => ({
  apiRequest: vi.fn(),
  createWorld: vi.fn(),
  generateStoryArc: vi.fn(),
  getChapterHistory: vi.fn(),
  getChapterHistoryDetail: vi.fn(),
  getNextChapterPrep: vi.fn(),
  getRelations: vi.fn(),
}));

const world: WorldOverview = {
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
  characters: [
    { id: 1, name: '林砚', role_type: 'protagonist', status: '开始调查密信', public_profile: {}, hidden_traits: {}, destiny_flag: null, current_goals: ['追查湿信来源'] },
  ],
  relations: [],
  foreshadows: [
    { id: 1, source_chapter_id: null, title: '裂纹玉佩', description: '玉佩出现裂纹。', foreshadow_type: 'item', status: 'advanced', urgency_level: 4, related_character_ids: [1], expected_resolution_window: null },
  ],
  recent_events: [],
  story_arc: [],
  approved_chapter_count: 1,
};

afterEach(() => cleanup());

beforeEach(() => {
  vi.mocked(apiRequest).mockReset();
  vi.mocked(getChapterHistory).mockReset();
  vi.mocked(getChapterHistoryDetail).mockReset();
  vi.mocked(getNextChapterPrep).mockReset();
  vi.mocked(getRelations).mockReset();
  vi.mocked(getRelations).mockResolvedValue([]);
  vi.mocked(apiRequest)
    .mockResolvedValueOnce([{ id: 7 }])
    .mockResolvedValueOnce(world);
  vi.mocked(getChapterHistory).mockResolvedValue({
    world_id: 7,
    chapters: [
      {
        id: 11,
        title: '第一章 雨巷密谈',
        status: 'approved',
        approved_version: 1,
        base_world_version: 1,
        world_version_after: 2,
        approved_excerpt: '林砚停在雨巷口。',
        event_count: 4,
        character_change_count: 1,
        foreshadow_change_count: 1,
      },
    ],
  });
  vi.mocked(getChapterHistoryDetail).mockResolvedValue({
    id: 11,
    world_id: 7,
    title: '第一章 雨巷密谈',
    status: 'approved',
    approved_version: 1,
    base_world_version: 1,
    approved_content: '林砚停在雨巷口。',
    world_version_before: 1,
    world_version_after: 2,
    events: [],
    character_changes: [],
    foreshadow_changes: [],
    critic_summary: null,
    character_arc_summary: null,
    execution_context: null,
  });
  vi.mocked(getNextChapterPrep).mockResolvedValue({
    world_id: 7,
    world_version: 2,
    next_chapter_number: 2,
    suggested_goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
    recommended_pov_character_id: 1,
    recommended_pov_character_name: '林砚',
    source_signals: ['character_arc_progression_hint'],
    priority_characters: [
      { character_id: 1, name: '林砚', role_type: 'protagonist', status: '开始调查密信', reason: '上一章提示。' },
    ],
    priority_foreshadows: [],
    progression_hints: [],
    continuity_warnings: [],
    recent_events: [],
  });
});

describe('WorldPage Narrative Control Center', () => {
  it('loads and displays Chapter History and Next Chapter Prep panels', async () => {
    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('Narrative Control Center')).toBeInTheDocument();
    expect(getChapterHistory).toHaveBeenCalledWith(7);
    expect(getNextChapterPrep).toHaveBeenCalledWith(7);
    expect(await screen.findByText('章节历史')).toBeInTheDocument();
    expect(screen.getByText('第一章 雨巷密谈 · v1 · 世界 1 → 2')).toBeInTheDocument();
    expect(screen.getByText('下一章准备台')).toBeInTheDocument();
    expect(screen.getByText('林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '用作下一章目标' }));
    expect(screen.getByText('已设为下一章目标：林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
  });

  it('shows degraded Narrative Control Center messages when panel APIs fail', async () => {
    vi.mocked(getChapterHistory).mockRejectedValueOnce(new Error('history down'));
    vi.mocked(getNextChapterPrep).mockRejectedValueOnce(new Error('prep down'));

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await waitFor(() => expect(getChapterHistory).toHaveBeenCalledWith(7));
    expect(await screen.findByText('章节历史暂不可用')).toBeInTheDocument();
    expect(await screen.findByText('下一章准备台暂不可用')).toBeInTheDocument();
  });

  it('renders RelationManager from the relations tab', async () => {
    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('青岚城')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '关系管理' }));

    expect(screen.getAllByText('关系管理').length).toBeGreaterThanOrEqual(2);
    expect(getRelations).toHaveBeenCalledWith(7);
    expect(screen.getByRole('button', { name: '+ 新增关系' })).toBeInTheDocument();
  });

  it('passes a selected next chapter goal when entering Studio from the regular button', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    await screen.findByText('Narrative Control Center');
    await user.click(screen.getByRole('button', { name: '用作下一章目标' }));
    await user.click(screen.getByRole('button', { name: '进入创作台' }));

    expect(onEnterStudio).toHaveBeenCalledWith(world, {
      initialChapterGoal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      executionContext: expect.objectContaining({
        source: 'next_chapter_prep',
        recommended_pov: { character_id: 1, name: '林砚' },
      }),
    });
  });

  it('enters Studio directly with the Next Chapter Prep suggested goal', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    await screen.findByText('Narrative Control Center');
    await user.click(screen.getByRole('button', { name: '进入创作台并使用此目标' }));

    expect(onEnterStudio).toHaveBeenCalledWith(world, {
      initialChapterGoal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      executionContext: expect.objectContaining({
        source: 'next_chapter_prep',
        recommended_pov: { character_id: 1, name: '林砚' },
      }),
    });
  });
});
