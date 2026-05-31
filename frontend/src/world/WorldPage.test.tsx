import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiRequest, compareWorldSnapshots, createSampleWorld, createWorld, createWorldFromSeed, createWorldSnapshot, exportWorldArchiveMarkdown, getArcPlan, getChapterHistory, getChapterHistoryDetail, getCharacters, getForeshadowLedger, getNarrativeHealth, getNextChapterPrep, getOpenThreads, getRelations, getWorldEvents, getWorldPulse, getWorldSeed, listWorldSeeds, listWorldSnapshots, searchWorld } from '../api/client';
import type { WorldOverview } from '../api/types';
import { WorldPage } from './WorldPage';

vi.mock('../api/client', () => ({
  apiRequest: vi.fn(),
  createSampleWorld: vi.fn(),
  compareWorldSnapshots: vi.fn(),
  createWorld: vi.fn(),
  createWorldFromSeed: vi.fn(),
  createWorldSnapshot: vi.fn(),
  exportWorldArchiveMarkdown: vi.fn(),
  generateStoryArc: vi.fn(),
  getChapterHistory: vi.fn(),
  getChapterHistoryDetail: vi.fn(),
  getNextChapterPrep: vi.fn(),
  getNarrativeHealth: vi.fn(),
  getOpenThreads: vi.fn(),
  getWorldEvents: vi.fn(),
  getWorldPulse: vi.fn(),
  getArcPlan: vi.fn(),
  getWorldSeed: vi.fn(),
  listWorldSeeds: vi.fn(),
  searchWorld: vi.fn(),
  getCharacters: vi.fn(),
  getForeshadowLedger: vi.fn(),
  getForeshadowTimeline: vi.fn(),
  getRelations: vi.fn(),
  listWorldSnapshots: vi.fn(),
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
  vi.mocked(compareWorldSnapshots).mockReset();
  vi.mocked(createSampleWorld).mockReset();
  vi.mocked(createWorld).mockReset();
  vi.mocked(createWorldFromSeed).mockReset();
  vi.mocked(createWorldSnapshot).mockReset();
  vi.mocked(exportWorldArchiveMarkdown).mockReset();
  vi.mocked(getChapterHistory).mockReset();
  vi.mocked(getChapterHistoryDetail).mockReset();
  vi.mocked(getNextChapterPrep).mockReset();
  vi.mocked(getNarrativeHealth).mockReset();
  vi.mocked(getOpenThreads).mockReset();
  vi.mocked(getWorldEvents).mockReset();
  vi.mocked(getWorldPulse).mockReset();
  vi.mocked(getArcPlan).mockReset();
  vi.mocked(getWorldSeed).mockReset();
  vi.mocked(listWorldSeeds).mockReset();
  vi.mocked(searchWorld).mockReset();
  vi.mocked(listWorldSnapshots).mockReset();
  vi.mocked(getCharacters).mockReset();
  vi.mocked(getForeshadowLedger).mockReset();
  vi.mocked(getRelations).mockReset();
  vi.mocked(getCharacters).mockResolvedValue(world.characters);
  vi.mocked(getForeshadowLedger).mockResolvedValue({
    world_id: 7,
    world_version: 2,
    summary: { total: 1, open_count: 1, planted_count: 0, advanced_count: 1, resolved_count: 0, expired_count: 0, high_urgency_count: 1, stale_count: 0, overdue_count: 0 },
    groups: {
      planted: [],
      advanced: [{
        foreshadow: world.foreshadows[0],
        status_group: 'advanced',
        is_open: true,
        is_high_urgency: true,
        is_stale: false,
        is_overdue: false,
        chapters_since_planted: 0,
        pressure_level: 'high',
        pressure_reasons: ['高紧迫度：4'],
        related_characters: [{ id: 1, name: '林砚', role_type: 'protagonist' }],
        recent_events: [],
      }],
      resolved: [],
      expired: [],
    },
    high_pressure: [],
  });
  vi.mocked(getRelations).mockResolvedValue([]);
  vi.mocked(apiRequest)
    .mockResolvedValueOnce([{ id: 7 }])
    .mockResolvedValueOnce(world);
  vi.mocked(listWorldSeeds).mockResolvedValue({
    seeds: [
      {
        key: 'forgotten-sun-city',
        label: '无日城',
        genre_template: 'weird_fantasy',
        hook: '所有人都忘记太阳存在过。',
        tension_profile: ['集体失忆'],
        starter_summary: { character_count: 1, relation_count: 0, foreshadow_count: 1, character_names: ['沈昼'], foreshadow_titles: ['空白日晷'] },
      },
    ],
  });
  vi.mocked(getWorldSeed).mockResolvedValue({
    key: 'forgotten-sun-city',
    label: '无日城',
    genre_template: 'weird_fantasy',
    hook: '所有人都忘记太阳存在过。',
    tension_profile: ['集体失忆'],
    starter_summary: { character_count: 1, relation_count: 0, foreshadow_count: 1, character_names: ['沈昼'], foreshadow_titles: ['空白日晷'] },
    payload: {
      title: '无日城',
      genre_template: 'weird_fantasy',
      truth_canon: '无日城没有太阳。',
      tone_profile: { style: '诡秘奇幻' },
      starter_assets: { characters: [{ name: '沈昼', role_type: 'protagonist' }], relations: [], foreshadows: [] },
    },
  });
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
  vi.mocked(getNarrativeHealth).mockResolvedValue({
    world_id: 7,
    world_version: 2,
    health_score: 88,
    status: 'healthy',
    summary: {},
    metrics: [{ key: 'approved_chapters', label: '已批准章节', value: 1, status: 'ok', detail: '已正式写入世界历史的章节数量。' }],
    risks: [],
    suggested_actions: [{ action_key: 'continue_next_chapter', label: '继续下一章', detail: '当前没有高风险阻塞。' }],
  });
  vi.mocked(getOpenThreads).mockResolvedValue({
    world_id: 7,
    world_version: 2,
    summary: {
      total_open_threads: 1,
      must_close_count: 0,
      should_advance_count: 1,
      can_delay_count: 0,
      can_leave_open_count: 0,
      convergence_ratio: 0,
      narrative_entropy_level: 'low',
      recent_event_count: 1,
    },
    threads: [
      {
        thread_id: 'foreshadow:1',
        thread_type: 'foreshadow',
        priority: 'should_advance',
        pressure_level: 'high',
        title: '裂纹玉佩',
        summary: '高紧迫度：4',
        related_object_type: 'foreshadow',
        related_object_id: 1,
        related_character_ids: [1],
        related_foreshadow_ids: [1],
        suggested_action: '下一章推进该伏笔。',
        can_seed_next_chapter_goal: true,
      },
    ],
    suggested_next_actions: [],
  });
  vi.mocked(getWorldPulse).mockResolvedValue({
    world_id: 7,
    world_version: 2,
    pulse_status: 'watch',
    primary_mode: 'converge',
    headline: 'World Pulse：开放线索压力较高。',
    indicators: [
      { key: 'open_threads', label: '开放线索', value: '1', status: 'watch', detail: '建议推进 1。' },
    ],
    focus: [],
    next_actions: [],
    source_summary: { approved_chapter_count: 1 },
  });
  vi.mocked(getArcPlan).mockResolvedValue({
    world_id: 7,
    world_version: 2,
    arc_mode: 'pressure',
    mode_reason: '存在应推进线索，可在有限扩张中继续加压。',
    expansion_budget: 'limited',
    next_chapter_number: 2,
    recommended_goal: '推进裂纹玉佩线索。',
    closure_items: [],
    guidance: [
      { guidance_key: 'increase_pressure', label: '继续加压', detail: '推进既有角色目标和高压伏笔。' },
    ],
    source_summary: { should_advance_count: 1 },
  });
  vi.mocked(getWorldEvents).mockResolvedValue({
    items: [],
    total: 0,
    limit: 20,
    offset: 0,
    summary: { total: 1, event_type_counts: { WORLD_CREATED: 1 }, latest_world_version: 2 },
  });
  vi.mocked(createWorldSnapshot).mockResolvedValue({ id: 12, world_id: 7, world_version: 2, label: null, note: null, created_at: '2026-05-31T00:00:00Z' });
  vi.mocked(exportWorldArchiveMarkdown).mockResolvedValue({ world_id: 7, world_version: 2, generated_at: '2026-05-31T00:00:00Z', archive_filename: 'WorldSim-test.zip', archive_base64: 'emlw', files: [] });
  vi.mocked(listWorldSnapshots).mockResolvedValue({
    world_id: 7,
    snapshots: [
      { id: 12, world_id: 7, world_version: 1, label: 'Before', note: null, created_at: '2026-05-31T00:00:00Z' },
      { id: 13, world_id: 7, world_version: 2, label: 'After', note: null, created_at: '2026-05-31T00:00:00Z' },
    ],
  });
  vi.mocked(compareWorldSnapshots).mockResolvedValue({
    world_id: 7,
    base_snapshot: { id: 12, world_id: 7, world_version: 1, label: 'Before', note: null, created_at: '2026-05-31T00:00:00Z' },
    target_snapshot: { id: 13, world_id: 7, world_version: 2, label: 'After', note: null, created_at: '2026-05-31T00:00:00Z' },
    summary: { total_changes: 1, object_type_counts: { character: 1 } },
    changes: { world: [], characters: [], relations: [], foreshadows: [], chapters: [], events: [] },
  });
});

describe('WorldPage world creation', () => {
  it('creates the built-in sample world and loads its overview', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(world);
    vi.mocked(createSampleWorld).mockResolvedValue({ id: 7 });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('创建世界工坊')).toBeInTheDocument();
    expect(await screen.findByText('Sandbox Seed Library')).toBeInTheDocument();
    expect(listWorldSeeds).toHaveBeenCalledOnce();
    await user.click(screen.getByRole('button', { name: '创建内置示例世界' }));

    expect(createSampleWorld).toHaveBeenCalledOnce();
    expect(apiRequest).toHaveBeenNthCalledWith(2, '/worlds/7/overview');
    expect(await screen.findByText('青岚城')).toBeInTheDocument();
  });

  it('shows backend validation errors when custom world creation fails', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest).mockResolvedValueOnce([]);
    vi.mocked(createWorld).mockRejectedValue(new Error('INVALID_CHARACTER_INDEX'));

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('创建世界工坊')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '创建自定义世界' }));

    expect(createWorld).toHaveBeenCalledOnce();
    expect(await screen.findByRole('alert')).toHaveTextContent('INVALID_CHARACTER_INDEX');
  });

  it('creates a world directly from a sandbox seed', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(world);
    vi.mocked(createWorldFromSeed).mockResolvedValue({ id: 7 });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('Sandbox Seed Library')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '直接创建此胚胎' }));

    expect(createWorldFromSeed).toHaveBeenCalledWith('forgotten-sun-city');
    expect(apiRequest).toHaveBeenNthCalledWith(2, '/worlds/7/overview');
    expect(await screen.findByText('青岚城')).toBeInTheDocument();
  });
});

describe('WorldPage Narrative Control Center', () => {
  it('loads and displays Chapter History and Next Chapter Prep panels', async () => {
    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('Narrative Control Center')).toBeInTheDocument();
    expect(getChapterHistory).toHaveBeenCalledWith(7);
    expect(getNextChapterPrep).toHaveBeenCalledWith(7);
    expect(getNarrativeHealth).toHaveBeenCalledWith(7);
    expect(getOpenThreads).toHaveBeenCalledWith(7);
    expect(getWorldPulse).toHaveBeenCalledWith(7);
    expect(getArcPlan).toHaveBeenCalledWith(7);
    expect(await screen.findByText('World Pulse')).toBeInTheDocument();
    expect(await screen.findByText('Arc Mode / Closure Plan')).toBeInTheDocument();
    expect(await screen.findByText('Narrative Health')).toBeInTheDocument();
    expect(await screen.findByText('Open Threads Board')).toBeInTheDocument();
    expect(await screen.findByText('章节历史')).toBeInTheDocument();
    expect(screen.getByText('第一章 雨巷密谈 · v1 · 世界 1 → 2')).toBeInTheDocument();
    expect(screen.getByText('下一章准备台')).toBeInTheDocument();
    expect(screen.getByText('林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
    expect(await screen.findByText('Timeline Explorer')).toBeInTheDocument();
    expect(getWorldEvents).toHaveBeenCalledWith(7, { limit: 20 });
    expect(await screen.findByText('Global Search')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '加载快照列表' }));
    expect(listWorldSnapshots).toHaveBeenCalledWith(7);

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

  it('renders World Bible Editor manager tabs with governance warning', async () => {
    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('青岚城')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '角色管理' }));
    expect(screen.getAllByText('角色管理').length).toBeGreaterThanOrEqual(2);
    expect(getCharacters).toHaveBeenCalledWith(7);
    expect(screen.getByText('这些编辑会正式写入世界状态，并使 world_version 增长。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '+ 新增角色' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '关系管理' }));
    expect(screen.getAllByText('关系管理').length).toBeGreaterThanOrEqual(2);
    expect(getRelations).toHaveBeenCalledWith(7);
    expect(screen.getByRole('button', { name: '+ 新增关系' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '伏笔账本' }));
    expect(screen.getAllByText('伏笔账本').length).toBeGreaterThanOrEqual(2);
    expect(getForeshadowLedger).toHaveBeenCalledWith(7);
    expect(await screen.findByText('Foreshadow Ledger')).toBeInTheDocument();
    expect(screen.getByText('伏笔治理台')).toBeInTheDocument();
    expect(screen.getByText('总数：1')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '+ 新增伏笔' })).toBeInTheDocument();
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
