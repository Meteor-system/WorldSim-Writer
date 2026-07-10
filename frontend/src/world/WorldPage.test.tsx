import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiRequest, assignWorldTag, bulkAssignWorldTag, compareWorldSnapshots, confirmWorldImport, createSampleWorld, createWorld, createWorldFromSeed, createWorldSnapshot, createWorldTag, deleteWorldTag, draftWorldFromBrief, exportWorldArchiveMarkdown, generateStoryArc, getActiveChapterSession, getArcPlan, getChapterHistory, getChapterHistoryDetail, getCharacters, getForeshadowLedger, getNarrativeHealth, getNextChapterPrep, getOpenThreads, getRelations, getSerialPlan, getWorldEvents, getWorldPulse, getWorldSeed, getWorldTag, listWorldImports, listWorldSeeds, listWorldSnapshots, listWorldTags, mergeWorldTag, previewWorldImport, searchWorld, unassignWorldTag, updateWorldStatus, updateWorldTag } from '../api/client';
import type { WorldCreateRequest, WorldOverview, WorldSearchResponse } from '../api/types';
import { WorldPage } from './WorldPage';

vi.mock('../api/client', () => ({
  apiRequest: vi.fn(),
  createSampleWorld: vi.fn(),
  compareWorldSnapshots: vi.fn(),
  confirmWorldImport: vi.fn(),
  assignWorldTag: vi.fn(),
  bulkAssignWorldTag: vi.fn(),
  createWorld: vi.fn(),
  createWorldFromSeed: vi.fn(),
  createWorldSnapshot: vi.fn(),
  createWorldTag: vi.fn(),
  deleteWorldTag: vi.fn(),
  draftWorldFromBrief: vi.fn(),
  exportWorldArchiveMarkdown: vi.fn(),
  generateStoryArc: vi.fn(),
  getActiveChapterSession: vi.fn(),
  getChapterHistory: vi.fn(),
  getChapterHistoryDetail: vi.fn(),
  getNextChapterPrep: vi.fn(),
  getNarrativeHealth: vi.fn(),
  getOpenThreads: vi.fn(),
  getSerialPlan: vi.fn(),
  getWorldEvents: vi.fn(),
  getWorldPulse: vi.fn(),
  getArcPlan: vi.fn(),
  getWorldSeed: vi.fn(),
  getWorldTag: vi.fn(),
  listWorldImports: vi.fn(),
  listWorldSeeds: vi.fn(),
  listWorldTags: vi.fn(),
  mergeWorldTag: vi.fn(),
  previewWorldImport: vi.fn(),
  previewStyleHandbook: vi.fn(),
  searchWorld: vi.fn(),
  unassignWorldTag: vi.fn(),
  updateWorldStatus: vi.fn(),
  updateWorldTag: vi.fn(),
  getCharacters: vi.fn(),
  getForeshadowLedger: vi.fn(),
  getForeshadowTimeline: vi.fn(),
  getRelations: vi.fn(),
  listWorldSnapshots: vi.fn(),
}));

const worldSearchResponse: WorldSearchResponse = {
  world_id: 7,
  query: '灯塔',
  object_type_counts: { character: 1 },
  results: [
    {
      object_type: 'character',
      object_id: 1,
      title: '林砚',
      subtitle: 'Character · protagonist',
      snippet: '林砚追查灯塔线索。',
      metadata: {},
    },
  ],
};

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

const newWorld: WorldOverview = {
  ...world,
  world_version: 1,
  approved_chapter_count: 0,
  story_arc: [],
  recent_events: [],
};

const briefDraftPayload: WorldCreateRequest = {
  title: '死因王国',
  genre_template: 'fantasy',
  truth_canon: '每个人出生时都会获得一个未来死因，死因记录支撑王国秩序。',
  tone_profile: { style: '黑暗奇幻悬疑', pacing: '高张力冷启动' },
  starter_assets: {
    characters: [
      { name: '伊莱', role_type: 'protagonist', public_profile: { identity: '命运抄写员' }, current_goals: ['查明死因被篡改的原因'] },
      { name: '维拉', role_type: 'rival', public_profile: { identity: '王国命运官' }, current_goals: ['封锁死因档案'] },
    ],
    relations: [{ source_index: 0, target_index: 1, relation_type: 'mutual_suspicion', intensity: 4, visibility: 'private' }],
    foreshadows: [{ title: '空白死因页', description: '伊莱的死因记录被银火烧穿。', foreshadow_type: 'fate_record_clue', status: 'planted', urgency_level: 4, related_character_indexes: [0, 1] }],
  },
};

const storyArcWorld: WorldOverview = {
  ...world,
  story_arc: Array.from({ length: 10 }, (_, index) => {
    const chapterNumber = index + 1;
    return {
      chapter_number: chapterNumber,
      title: `第 ${chapterNumber} 章标题`,
      summary: `第 ${chapterNumber} 章摘要：林砚推进裂纹玉佩线索。`,
      core_conflict: `第 ${chapterNumber} 章核心冲突详情`,
      pov_suggestion: `第 ${chapterNumber} 章 POV 建议`,
      foreshadow_hints: chapterNumber === 1 ? ['裂纹玉佩', '雨巷铜铃'] : [],
    };
  }),
};

const secondWorld: WorldOverview = {
  ...world,
  id: 8,
  title: '星舰余烬',
  genre_template: 'sci_fi',
  truth_canon: '星舰仍在航行。',
  world_version: 1,
  status: 'active',
};

const archivedWorld: WorldOverview = {
  ...world,
  status: 'archived',
};

afterEach(() => cleanup());

beforeEach(() => {
  vi.mocked(apiRequest).mockReset();
  vi.mocked(compareWorldSnapshots).mockReset();
  vi.mocked(confirmWorldImport).mockReset();
  vi.mocked(createSampleWorld).mockReset();
  vi.mocked(createWorld).mockReset();
  vi.mocked(assignWorldTag).mockReset();
  vi.mocked(bulkAssignWorldTag).mockReset();
  vi.mocked(createWorldFromSeed).mockReset();
  vi.mocked(createWorldSnapshot).mockReset();
  vi.mocked(createWorldTag).mockReset();
  vi.mocked(deleteWorldTag).mockReset();
  vi.mocked(draftWorldFromBrief).mockReset();
  vi.mocked(exportWorldArchiveMarkdown).mockReset();
  vi.mocked(generateStoryArc).mockReset();
  vi.mocked(getActiveChapterSession).mockReset();
  vi.mocked(getActiveChapterSession).mockResolvedValue({ chapter: null, draft: null, draft_versions: [] });
  vi.mocked(getChapterHistory).mockReset();
  vi.mocked(getChapterHistoryDetail).mockReset();
  vi.mocked(getNextChapterPrep).mockReset();
  vi.mocked(getNarrativeHealth).mockReset();
  vi.mocked(getOpenThreads).mockReset();
  vi.mocked(getSerialPlan).mockReset();
  vi.mocked(getWorldEvents).mockReset();
  vi.mocked(getWorldPulse).mockReset();
  vi.mocked(getArcPlan).mockReset();
  vi.mocked(getWorldSeed).mockReset();
  vi.mocked(getWorldTag).mockReset();
  vi.mocked(listWorldImports).mockReset();
  vi.mocked(listWorldSeeds).mockReset();
  vi.mocked(listWorldTags).mockReset();
  vi.mocked(mergeWorldTag).mockReset();
  vi.mocked(previewWorldImport).mockReset();
  vi.mocked(searchWorld).mockReset();
  vi.mocked(searchWorld).mockResolvedValue(worldSearchResponse);
  vi.mocked(listWorldImports).mockResolvedValue({ world_id: 7, batches: [] });
  vi.mocked(unassignWorldTag).mockReset();
  vi.mocked(updateWorldStatus).mockReset();
  vi.mocked(updateWorldTag).mockReset();
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
        starter_guidance: {
          first_chapter_goal: '确认空白日晷为何没有影子。',
          protagonist_relationships: ['沈昼独自追查太阳禁忌。'],
          foreshadow_pressure: ['空白日晷需要在开篇建立危险感。'],
          story_health_hints: ['确认前不写入正史，只作为开篇参考。'],
        },
      },
    ],
  });
  vi.mocked(listWorldTags).mockResolvedValue({
    world_id: 7,
    tags: [
      {
        id: 3,
        world_id: 7,
        name: '灯塔线',
        slug: '灯塔线',
        color: 'amber',
        created_at: '2026-05-31T00:00:00Z',
        assignment_count: 1,
        object_type_counts: { character: 1 },
      },
    ],
  });
  vi.mocked(createWorldTag).mockResolvedValue({ id: 3, world_id: 7, name: '灯塔线', slug: '灯塔线', color: 'amber', created_at: '2026-05-31T00:00:00Z' });
  vi.mocked(getWorldTag).mockResolvedValue({
    tag: {
      id: 3,
      world_id: 7,
      name: '灯塔线',
      slug: '灯塔线',
      color: 'amber',
      created_at: '2026-05-31T00:00:00Z',
      assignment_count: 1,
      object_type_counts: { character: 1 },
    },
    objects: [],
  });
  vi.mocked(assignWorldTag).mockResolvedValue({ id: 9, world_id: 7, tag_id: 3, object_type: 'character', object_id: 1, created_at: '2026-05-31T00:00:00Z' });
  vi.mocked(bulkAssignWorldTag).mockResolvedValue({ world_id: 7, tag_id: 3, object_type: 'character', requested_count: 2, assigned_count: 2, already_assigned_count: 0, assigned_object_ids: [1, 2], already_assigned_object_ids: [] });
  vi.mocked(unassignWorldTag).mockResolvedValue(undefined);
  vi.mocked(updateWorldTag).mockResolvedValue({ id: 3, world_id: 7, name: '灯塔线', slug: '灯塔线', color: 'amber', created_at: '2026-05-31T00:00:00Z' });
  vi.mocked(mergeWorldTag).mockResolvedValue({ world_id: 7, source_tag_id: 3, target_tag_id: 4, moved_count: 1, already_assigned_count: 0, deleted_source_tag: true });
  vi.mocked(deleteWorldTag).mockResolvedValue(undefined);
  vi.mocked(getWorldSeed).mockResolvedValue({
    key: 'forgotten-sun-city',
    label: '无日城',
    genre_template: 'weird_fantasy',
    hook: '所有人都忘记太阳存在过。',
    tension_profile: ['集体失忆'],
    starter_summary: { character_count: 1, relation_count: 0, foreshadow_count: 1, character_names: ['沈昼'], foreshadow_titles: ['空白日晷'] },
    starter_guidance: {
      first_chapter_goal: '确认空白日晷为何没有影子。',
      protagonist_relationships: ['沈昼独自追查太阳禁忌。'],
      foreshadow_pressure: ['空白日晷需要在开篇建立危险感。'],
      story_health_hints: ['确认前不写入正史，只作为开篇参考。'],
    },
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
    material_references: [],
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
    headline: '世界近况：开放线索压力较高。',
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
  vi.mocked(exportWorldArchiveMarkdown).mockResolvedValue({
    world_id: 7,
    world_version: 2,
    generated_at: '2026-05-31T00:00:00Z',
    archive_filename: 'WorldSim-test.zip',
    archive_format: 'zip',
    archive_encoding: 'base64',
    archive_base64: 'emlw',
    files_are_inline: true,
    files: [],
  });
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

describe('WorldPage operations dashboard', () => {
  it('localizes overview headers, genre, and status without raw identifiers', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('世界正史档案')).toBeInTheDocument();
    expect(screen.getByText('第 2 版 · 仙侠 · 进行中')).toBeInTheDocument();
    expect(screen.getByText('今日创作')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('WORLD CANON');
    expect(document.body).not.toHaveTextContent('World Canon');
    expect(document.body).not.toHaveTextContent('WORLD OPERATIONS');
    expect(document.body).not.toHaveTextContent('World Operations');
    expect(document.body).not.toHaveTextContent('xianxia');
    expect(document.body).not.toHaveTextContent('running');
  });

  it('shows world operations metrics in user language', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('今日创作看板'));
    expect(dashboard.getByText('今日创作看板')).toBeInTheDocument();
    expect(dashboard.getByText('世界进度：第 2 版')).toBeInTheDocument();
    expect(dashboard.getByText('已写入正史章节：1')).toBeInTheDocument();
    expect(dashboard.getByText('近期世界历史记录：0')).toBeInTheDocument();
    expect(dashboard.getByText('待处理悬念/伏笔：1')).toBeInTheDocument();
  });

  it('recommends explainable next actions from current world data', async () => {
    const onEnterStudio = vi.fn();
    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('今日创作看板'));
    expect(dashboard.getByText('今天建议处理什么')).toBeInTheDocument();
    expect(dashboard.getByText('继续下一章')).toBeInTheDocument();
    expect(dashboard.getByText('回收或推进悬念/伏笔')).toBeInTheDocument();

    await user.click(dashboard.getByRole('button', { name: '继续下一章' }));
    expect(onEnterStudio).toHaveBeenCalledWith(world, {
      initialChapterGoal: undefined,
      executionContext: undefined,
    });
  });

  it('summarizes active roles and urgent suspense without hardcoded generated prose', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('今日创作看板'));
    expect(dashboard.getByText('活跃角色')).toBeInTheDocument();
    expect(dashboard.getByText('林砚：追查湿信来源')).toBeInTheDocument();
    expect(dashboard.getByText('紧迫悬念/伏笔')).toBeInTheDocument();
    expect(dashboard.getByText('裂纹玉佩：推进中 · 紧迫度 4')).toBeInTheDocument();
    expect(dashboard.getByTestId('world-dashboard-actions')).toHaveClass('gap-4');
    expect(dashboard.getByTestId('world-dashboard-sidebars')).toHaveClass('gap-5');
    expect(document.body).not.toHaveTextContent('WORLD OPERATIONS');
    expect(document.body).not.toHaveTextContent('World Operations');
    expect(dashboard.getByText('近期世界历史记录')).toBeInTheDocument();
    expect(dashboard.queryByText('第一章 雨巷密谈')).not.toBeInTheDocument();
    expect(dashboard.queryByText('林砚停在雨巷口。')).not.toBeInTheDocument();
  });

  it('does not load narrative tab data before the user opens those tabs', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('世界正史档案')).toBeInTheDocument();
    expect(getNextChapterPrep).not.toHaveBeenCalled();
    expect(getWorldPulse).not.toHaveBeenCalled();
    expect(getArcPlan).not.toHaveBeenCalled();
    expect(getNarrativeHealth).not.toHaveBeenCalled();
    expect(getOpenThreads).not.toHaveBeenCalled();
    expect(getChapterHistory).not.toHaveBeenCalled();
  });

  it('shows a focused first-chapter onboarding card for new worlds and hides it after arc generation', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(newWorld);
    vi.mocked(generateStoryArc).mockResolvedValueOnce({
      world_id: 7,
      story_arc: storyArcWorld.story_arc,
    });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    const onboarding = within(await screen.findByLabelText('第一章写作引导'));
    expect(onboarding.getByText('生成故事大纲 → 写第一章')).toBeInTheDocument();
    expect(onboarding.getByText('这本小说还没有写入正史。先生成前 10 章故事弧线，再用第一章目标进入创作台。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '继续下一章' })).not.toBeInTheDocument();

    await user.click(onboarding.getByRole('button', { name: '生成故事大纲' }));

    expect(generateStoryArc).toHaveBeenCalledWith(7);
    expect(await screen.findByRole('button', { name: '继续下一章' })).toBeInTheDocument();
    expect(screen.queryByLabelText('第一章写作引导')).not.toBeInTheDocument();
  });
});

describe('WorldPage world creation', () => {
  it('shows the newcomer three-minute loop and high-tension embryo entry', async () => {
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest).mockResolvedValueOnce([]);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('3 分钟开始写你的故事世界')).toBeInTheDocument();
    expect(screen.getByText('选灵感模板')).toBeInTheDocument();
    expect(screen.getByText('生成第一章')).toBeInTheDocument();
    expect(screen.getByText('写入正史')).toBeInTheDocument();
    expect(screen.getByText('查看世界变化')).toBeInTheDocument();
    expect(await screen.findByText('高张力灵感模板')).toBeInTheDocument();
  });

  it('creates a high-tension embryo without treating seed hook as generated chapter content', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(world);
    vi.mocked(createWorldFromSeed).mockResolvedValue({ id: 7 });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('所有人都忘记太阳存在过。')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '直接创建此模板' }));

    expect(createWorldFromSeed).toHaveBeenCalledWith('forgotten-sun-city');
    expect(await screen.findByText('青岚城')).toBeInTheDocument();
    expect(screen.queryByText('Writer Draft')).not.toBeInTheDocument();
    expect(screen.queryByText('世界推进结算')).not.toBeInTheDocument();
  });

  it('aligns the first chapter launchpad with the three-minute loop', async () => {
    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '继续创作' }));

    expect(await screen.findByText('第一章起点')).toBeInTheDocument();
    expect(screen.getByText('生成第一章 → 写入正史 → 查看世界变化')).toBeInTheDocument();
    expect(screen.getByText('素材导入节点')).toBeInTheDocument();
    expect(listWorldImports).toHaveBeenCalledWith(7);
  });

  it('opens the creation form with import node materials as read-only brief references', async () => {
    const user = userEvent.setup();
    const importBatchResponse = {
      world_id: 7,
      batches: [
        {
          id: 9,
          world_id: 7,
          source_type: 'pasted_text' as const,
          source_title: '旧素材摘录',
          original_excerpt: '原文不会进入开书草稿。',
          cleaned_excerpt: '清洗片段。',
          status: 'confirmed' as const,
          asset_counts: { inspiration: 1 },
          conflicts: [],
          created_at: '2026-05-31T00:00:00Z',
          confirmed_at: '2026-05-31T00:00:00Z',
          assets: [
            {
              id: 42,
              world_id: 7,
              batch_id: 9,
              status: 'candidate' as const,
              asset_pool: 'inspiration' as const,
              title: '雾港钟楼候选素材',
              summary: '一座每天倒敲十三次的钟楼引发城内记忆错位。',
              raw_text: '不应传入一句话开书。',
              metadata: {},
              created_at: '2026-05-31T00:00:00Z',
            },
          ],
        },
      ],
    };
    vi.mocked(listWorldImports)
      .mockResolvedValueOnce(importBatchResponse)
      .mockResolvedValueOnce(importBatchResponse);
    vi.mocked(draftWorldFromBrief).mockResolvedValueOnce({
      source_brief: '一个边境殖民地依赖濒临失控的跃迁灯塔',
      draft: briefDraftPayload,
      first_chapter_goal: '让伊莱发现自己的死因记录被烧穿。',
      generation_notes: ['已参考候选素材提炼原创方向。'],
      safety_notes: ['候选素材只读，不会写入 canon/正史或 EventLog。'],
      material_references: [
        {
          source: 'import_node',
          asset_id: 42,
          title: '雾港钟楼候选素材',
          summary: '一座每天倒敲十三次的钟楼引发城内记忆错位。',
          asset_pool: 'inspiration',
          source_rights: 'general_reference',
        },
      ],
    });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '继续创作' }));
    expect(await screen.findByText(/不带入原文，不会创建世界/)).toBeInTheDocument();
    await user.click(await screen.findByRole('button', { name: '用候选素材开新书草稿' }));

    expect(await screen.findByText('Import Node 候选素材参考（只读）')).toBeInTheDocument();
    expect(screen.getByLabelText('Import Node 候选素材参考')).toHaveTextContent('雾港钟楼候选素材');
    expect(screen.getByLabelText('Import Node 候选素材参考')).toHaveTextContent('只会发送标题、摘要、素材池和来源权利，不发送原文');
    expect(screen.getByLabelText('Import Node 候选素材参考')).toHaveTextContent('不会创建世界、不会写入 canon/正史，也不会写入 EventLog');
    expect(screen.getByLabelText('Import Node 候选素材参考')).not.toHaveTextContent('不应传入一句话开书');

    await user.type(screen.getByLabelText('一句话故事想法'), '一个边境殖民地依赖濒临失控的跃迁灯塔');
    await user.click(screen.getByRole('button', { name: '生成世界创建草稿' }));

    expect(draftWorldFromBrief).toHaveBeenCalledWith(
      '一个边境殖民地依赖濒临失控的跃迁灯塔',
      null,
      3,
      [
        {
          source: 'import_node',
          asset_id: 42,
          title: '雾港钟楼候选素材',
          summary: '一座每天倒敲十三次的钟楼引发城内记忆错位。',
          asset_pool: 'inspiration',
          source_rights: 'general_reference',
        },
      ],
    );
    expect(await screen.findByLabelText('本次草稿引用的候选素材')).toHaveTextContent('只使用标题、摘要、素材池和来源权利，不使用原文');
    expect(screen.getByLabelText('本次草稿引用的候选素材')).toHaveTextContent('不会创建世界、写入 canon/正史或写入 EventLog');
  });

  it('creates the built-in sample world and loads its overview', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(world);
    vi.mocked(createSampleWorld).mockResolvedValue({ id: 7 });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('创建世界工坊')).toBeInTheDocument();
    expect(await screen.findByText('灵感模板库')).toBeInTheDocument();
    expect(listWorldSeeds).toHaveBeenCalledOnce();
    await user.click(screen.getByRole('button', { name: '创建内置示例世界' }));

    expect(createSampleWorld).toHaveBeenCalledOnce();
    expect(apiRequest).toHaveBeenNthCalledWith(2, '/worlds/7/overview');
    expect(await screen.findByText('青岚城')).toBeInTheDocument();
  });

  it('offers a first-chapter Studio draft CTA after creating from a brief draft', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(newWorld);
    vi.mocked(draftWorldFromBrief).mockResolvedValueOnce({
      source_brief: '一个所有人出生时都会被分配死因的王国',
      draft: briefDraftPayload,
      first_chapter_goal: '让伊莱发现自己的死因记录被烧穿。',
      generation_notes: ['已生成可编辑草稿。'],
      safety_notes: ['确认前不会创建世界、写入正史或推进世界进度。'],
    });
    vi.mocked(createWorld).mockResolvedValueOnce({ id: 7 });

    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    expect(await screen.findByText('创建世界工坊')).toBeInTheDocument();
    await user.type(screen.getByLabelText('一句话故事想法'), '一个所有人出生时都会被分配死因的王国');
    await user.click(screen.getByRole('button', { name: '生成世界创建草稿' }));
    await user.click(await screen.findByRole('button', { name: '创建自定义世界' }));

    expect(createWorld).toHaveBeenCalledWith(expect.objectContaining({ title: '死因王国' }));
    expect(await screen.findByLabelText('创建草稿第一章入口')).toBeInTheDocument();
    expect(screen.getByText('只会在 Studio 创建章节草稿与审批预览；确认前不会写入正史或推进世界进度。')).toBeInTheDocument();
    expect(onEnterStudio).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: '生成第一章草稿并进入 Studio' }));

    expect(onEnterStudio).toHaveBeenCalledWith(newWorld, {
      initialChapterGoal: '让伊莱发现自己的死因记录被烧穿。',
      executionContext: expect.objectContaining({
        source: 'manual',
        source_world_version: 1,
        next_chapter_number: 1,
        goal: '让伊莱发现自己的死因记录被烧穿。',
        recommended_pov: { character_id: null, name: null },
        source_signals: ['world_creation_draft'],
      }),
      autoDraftFirstChapter: true,
    });
  });

  it('restores an unfinished chapter after reopening the world and resumes Studio without creating a duplicate', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    const activeSession = {
      chapter: {
        id: 11,
        world_id: 7,
        title: '第一章 雨巷密谈',
        status: 'outlined',
        draft_version: 1,
        approved_version: null,
        base_world_version: 1,
        approved_content: null,
        chapter_goal: '让林砚在雨巷第一次试探沈微霜。',
        outline_beats: [{ beat_id: 'beat-1', summary: '雨巷试探', pov_character: '林砚', location: '雨巷', emotional_arc: '警觉 -> 犹疑', key_dialogue_hints: [] }],
        outline_context: { core_conflict: '判断沈微霜是否可信' },
        critique_report: {},
        execution_context: null,
      },
      draft: null,
      draft_versions: [],
    };
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest).mockResolvedValueOnce([newWorld]).mockResolvedValueOnce(newWorld);
    vi.mocked(getActiveChapterSession).mockResolvedValueOnce(activeSession);

    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    expect(await screen.findByLabelText('进行中章节入口')).toHaveTextContent('已恢复到 outlined 阶段');
    expect(screen.getByLabelText('进行中章节入口')).toHaveTextContent('不会创建重复章节');
    await user.click(screen.getByRole('button', { name: '继续进入 Studio' }));

    expect(onEnterStudio).toHaveBeenCalledWith(newWorld, {
      initialChapterGoal: '让林砚在雨巷第一次试探沈微霜。',
      executionContext: undefined,
      autoDraftFirstChapter: true,
      resumeSession: activeSession,
    });
  });

  it('routes dashboard and story-arc chapter launches back to the same active Studio session', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    const frozenExecutionContext = {
      source: 'manual' as const,
      source_world_version: 2,
      next_chapter_number: 2,
      goal: '保留原有章节目标',
      recommended_pov: { character_id: 1, name: '林砚' },
      priority_characters: [],
      priority_foreshadows: [],
      progression_hints: [],
      continuity_warnings: [],
      recent_events: [],
      source_signals: ['manual'],
      material_references: [],
    };
    const activeSession = {
      chapter: {
        id: 11,
        world_id: 7,
        title: '第二章 保留中的章节',
        status: 'drafting',
        draft_version: 1,
        approved_version: null,
        base_world_version: 2,
        approved_content: null,
        chapter_goal: frozenExecutionContext.goal,
        outline_beats: [],
        outline_context: {},
        critique_report: {},
        execution_context: frozenExecutionContext,
      },
      draft: null,
      draft_versions: [],
      recent_approval: null,
    };
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest).mockResolvedValueOnce([{ id: 7 }]).mockResolvedValueOnce(storyArcWorld);
    vi.mocked(getActiveChapterSession).mockResolvedValueOnce(activeSession);
    vi.mocked(getSerialPlan).mockResolvedValueOnce({
      world_id: 7,
      world_version: 2,
      approved_chapter_count: 1,
      queue: [{
        chapter_number: 2,
        title: '替代连载目标',
        goal: '不应覆盖原有目标',
        summary: '替代摘要',
        core_conflict: '替代冲突',
        pov_suggestion: '沈微霜',
        foreshadow_hints: [],
        source: 'story_arc',
      }],
      safety_notes: [],
      review_guardrails: [],
      convergence_guidance: {
        mode: 'expand',
        mode_label: '允许扩张',
        open_foreshadow_count: 0,
        high_pressure_count: 0,
        stale_count: 0,
        overdue_count: 0,
        priority_foreshadows: [],
        recommendation: '可继续扩张。',
        guidance_notes: [],
      },
    });

    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('今日创作看板'));
    await user.click(dashboard.getByRole('button', { name: '继续进行中的章节' }));
    expect(onEnterStudio).toHaveBeenLastCalledWith(storyArcWorld, {
      initialChapterGoal: frozenExecutionContext.goal,
      executionContext: frozenExecutionContext,
      autoDraftFirstChapter: true,
      resumeSession: activeSession,
    });

    await user.click(screen.getByRole('button', { name: '继续创作' }));
    await user.click(await screen.findByRole('button', { name: '用此目标进入创作台' }));
    expect(onEnterStudio).toHaveBeenLastCalledWith(storyArcWorld, {
      initialChapterGoal: frozenExecutionContext.goal,
      executionContext: frozenExecutionContext,
      autoDraftFirstChapter: true,
      resumeSession: activeSession,
    });

    await user.click(screen.getByRole('button', { name: '生成连载队列' }));
    await user.click(await screen.findByRole('button', { name: '用此目标进入 Studio' }));
    expect(onEnterStudio).toHaveBeenLastCalledWith(storyArcWorld, {
      initialChapterGoal: frozenExecutionContext.goal,
      executionContext: frozenExecutionContext,
      autoDraftFirstChapter: true,
      resumeSession: activeSession,
    });
    expect(onEnterStudio).toHaveBeenCalledTimes(3);
  });

  it('restores the latest approval settlement after reopening without exposing another approval action', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    const recentApproval = {
      chapter_id: 11,
      title: '第一章 雨巷密谈',
      approved_version: 1,
      world_version_before: 1,
      world_version_after: 2,
      character_change_count: 1,
      foreshadow_change_count: 1,
    };
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest).mockResolvedValueOnce([newWorld]).mockResolvedValueOnce(newWorld);
    vi.mocked(getActiveChapterSession).mockResolvedValueOnce({
      chapter: null,
      draft: null,
      draft_versions: [],
      recent_approval: recentApproval,
    });

    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    expect(await screen.findByLabelText('最近世界推进结算入口')).toHaveTextContent('本章已写入正史并推进到第 2 版');
    expect(screen.queryByLabelText('进行中章节入口')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '查看最近世界推进结算' }));

    expect(onEnterStudio).toHaveBeenCalledWith(newWorld, { recentApproval });
  });

  it('explains multiple unfinished chapters and keeps all new chapter entries closed', async () => {
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest).mockResolvedValueOnce([newWorld]).mockResolvedValueOnce(newWorld);
    vi.mocked(getActiveChapterSession).mockRejectedValueOnce(new Error('MULTIPLE_ACTIVE_CHAPTERS'));

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByRole('alert')).toHaveTextContent('检测到多个未完成章节，已停止自动恢复和新建章节');
    expect(screen.queryByText('世界正史档案')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '继续下一章' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '生成第一章草稿并进入 Studio' })).not.toBeInTheDocument();
  });

  it('does not open a world or new chapter entry when active-session recovery fails', async () => {
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest).mockResolvedValueOnce([newWorld]).mockResolvedValueOnce(newWorld);
    vi.mocked(getActiveChapterSession).mockRejectedValueOnce(new Error('进行中章节恢复失败'));

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByRole('alert')).toHaveTextContent('进行中章节恢复失败');
    expect(screen.queryByText('世界正史档案')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '继续下一章' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '生成第一章草稿并进入 Studio' })).not.toBeInTheDocument();
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

    expect(await screen.findByText('灵感模板库')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '直接创建此模板' }));

    expect(createWorldFromSeed).toHaveBeenCalledWith('forgotten-sun-city');
    expect(apiRequest).toHaveBeenNthCalledWith(2, '/worlds/7/overview');
    expect(await screen.findByText('青岚城')).toBeInTheDocument();
  });
});

describe('WorldPage bookshelf', () => {
  it('shows a bookshelf for multiple worlds and opens the selected second world', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([
        { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'active', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
        { id: 8, title: '星舰余烬', genre_template: 'sci_fi', truth_canon: '星舰仍在航行。', truth_canon_version: 1, world_version: 1, status: 'active', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
      ])
      .mockResolvedValueOnce(secondWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('作品书架')).toBeInTheDocument();
    expect(screen.queryByText('世界正史档案')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '打开 星舰余烬' }));

    expect(await screen.findByText('星舰余烬')).toBeInTheDocument();
    expect(apiRequest).toHaveBeenNthCalledWith(2, '/worlds/8/overview');
  });

  it('returns from an open world to the bookshelf', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([
        { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'active', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
        { id: 8, title: '星舰余烬', genre_template: 'sci_fi', truth_canon: '星舰仍在航行。', truth_canon_version: 1, world_version: 1, status: 'active', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
      ])
      .mockResolvedValueOnce(world);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '打开 青岚城' }));
    expect(await screen.findByText('世界正史档案')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '返回作品书架' }));

    expect(screen.getByText('作品书架')).toBeInTheDocument();
  });

  it('shows archive entry copy on the current world page', async () => {
    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '归档导出' }));

    expect(await screen.findByText('归档前建议先创建世界快照并导出 Markdown ZIP。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '归档当前小说' })).toBeInTheDocument();
  });

  it('can archive and restore the current world without leaving the page', async () => {
    const user = userEvent.setup();
    vi.mocked(updateWorldStatus)
      .mockResolvedValueOnce({ ...world, status: 'archived' })
      .mockResolvedValueOnce({ ...world, status: 'active' });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '归档导出' }));
    await user.click(await screen.findByRole('button', { name: '归档当前小说' }));

    expect(updateWorldStatus).toHaveBeenCalledWith(7, { status: 'archived' });
    expect(await screen.findByRole('button', { name: '取消归档当前小说' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '取消归档当前小说' }));

    expect(updateWorldStatus).toHaveBeenCalledWith(7, { status: 'active' });
    expect(await screen.findByRole('button', { name: '归档当前小说' })).toBeInTheDocument();
  });

  it('shows the bookshelf instead of auto-opening a single archived world', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([
        { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
      ])
      .mockResolvedValueOnce(archivedWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('作品书架')).toBeInTheDocument();
    expect(screen.queryByText('世界正史档案')).not.toBeInTheDocument();
    expect(screen.getByText('已归档')).toBeInTheDocument();
    expect(screen.getByText('青岚城')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '打开 青岚城' }));

    expect(await screen.findByText('世界正史档案')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '归档导出' }));
    expect(screen.getByRole('button', { name: '取消归档当前小说' })).toBeInTheDocument();
  });

  it('restores an archived world directly from the bookshelf', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest).mockResolvedValueOnce([
      { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
      { id: 8, title: '星舰余烬', genre_template: 'sci_fi', truth_canon: '星舰仍在航行。', truth_canon_version: 1, world_version: 1, status: 'active', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
    ]);
    vi.mocked(updateWorldStatus).mockResolvedValueOnce({ ...archivedWorld, status: 'active' });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('作品书架')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '恢复写作 青岚城' }));

    expect(updateWorldStatus).toHaveBeenCalledWith(7, { status: 'active' });
    expect(await screen.findByText('第 2 版 · 仙侠 · 进行中')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('xianxia');
    expect(document.body).not.toHaveTextContent('active');
    expect(screen.getByRole('button', { name: '打开 青岚城' })).toBeInTheDocument();
    expect(screen.getByText('暂无归档小说。')).toBeInTheDocument();
  });

  it('shows a paused state when opening an archived world', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([
        { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
      ])
      .mockResolvedValueOnce(archivedWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '打开 青岚城' }));

    expect(await screen.findByText('已归档：写作已暂停')).toBeInTheDocument();
    expect(screen.getByText('这本小说已从活跃创作中移出。快照、章节、伏笔和导出都还在。恢复写作后再进入创作台。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '恢复写作' })).toBeInTheDocument();
    expect(screen.queryByText('第一章起点')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '进入创作台' })).not.toBeInTheDocument();
  });

  it('restores writing from the archived paused state', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([
        { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
      ])
      .mockResolvedValueOnce(archivedWorld);
    vi.mocked(updateWorldStatus).mockResolvedValueOnce({ ...world, status: 'active' });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '打开 青岚城' }));
    await user.click(await screen.findByRole('button', { name: '恢复写作' }));

    expect(updateWorldStatus).toHaveBeenCalledWith(7, { status: 'active' });
    await user.click(screen.getByRole('button', { name: '继续创作' }));
    expect(await screen.findByText('第一章起点')).toBeInTheDocument();
    expect(screen.queryByText('已归档：写作已暂停')).not.toBeInTheDocument();
  });

  it('returns from a single auto-opened world to the bookshelf', async () => {
    const user = userEvent.setup();

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('世界正史档案')).toBeInTheDocument();
    expect(screen.queryByText('作品书架')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '返回作品书架' }));

    expect(screen.getByText('作品书架')).toBeInTheDocument();
    expect(screen.getByText('青岚城')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建新小说' })).toBeInTheDocument();
  });

  it('opens the creation form from a single-world bookshelf', async () => {
    const user = userEvent.setup();

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '返回作品书架' }));
    await user.click(screen.getByRole('button', { name: '创建新小说' }));

    expect(await screen.findByText('创建世界工坊')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '返回作品书架' })).toBeInTheDocument();
    expect(listWorldSeeds).toHaveBeenCalled();
  });

  it('still auto-opens a single existing world', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('世界正史档案')).toBeInTheDocument();
    expect(screen.queryByText('作品书架')).not.toBeInTheDocument();
  });
});

describe('WorldPage Story Arc Planner', () => {
  async function openWriteTab(user: ReturnType<typeof userEvent.setup>) {
    await user.click(await screen.findByRole('button', { name: '继续创作' }));
  }

  it('shows a first chapter launchpad that can generate an arc when no story arc exists', async () => {
    const user = userEvent.setup();
    vi.mocked(generateStoryArc).mockResolvedValueOnce({
      world_id: 7,
      story_arc: storyArcWorld.story_arc,
    });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);
    await openWriteTab(user);

    expect(await screen.findByText('第一章起点')).toBeInTheDocument();
    expect(screen.getByText('先生成前 10 章故事弧线，再把下一章目标带入创作台。')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '生成第一轮故事弧线' }));

    expect(generateStoryArc).toHaveBeenCalledWith(7);
    expect(await screen.findByText('第 2 章标题')).toBeInTheDocument();
  });

  it('shows story-operation waiting copy while generating the story arc', async () => {
    const user = userEvent.setup();
    let resolveStoryArc!: (value: Awaited<ReturnType<typeof generateStoryArc>>) => void;
    vi.mocked(generateStoryArc).mockImplementationOnce(async () => new Promise<Awaited<ReturnType<typeof generateStoryArc>>>((resolve) => {
      resolveStoryArc = resolve;
    }));

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);
    await openWriteTab(user);

    await user.click(await screen.findByRole('button', { name: '生成第一轮故事弧线' }));
    expect((await screen.findAllByRole('button', { name: '故事弧线规划中…' })).length).toBeGreaterThan(0);

    resolveStoryArc({ world_id: 7, story_arc: storyArcWorld.story_arc });
    expect(await screen.findByText('第 2 章标题')).toBeInTheDocument();
  });

  it('shows the next unapproved story arc chapter in the launchpad', async () => {
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);

    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);
    await openWriteTab(user);

    expect(await screen.findByText('第一章起点')).toBeInTheDocument();
    expect(screen.getByText('下一章 · 第 2 章')).toBeInTheDocument();
    expect(screen.getByText('第 2 章标题')).toBeInTheDocument();
    expect(screen.queryByText('下一章 · 第 1 章')).not.toBeInTheDocument();
  });

  it('launches Studio with the selected story arc chapter goal', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);

    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);
    await openWriteTab(user);

    await user.click(await screen.findByRole('button', { name: '用此目标进入创作台' }));

    expect(onEnterStudio).toHaveBeenCalledWith(storyArcWorld, {
      initialChapterGoal: '第 2 章标题：第 2 章摘要：林砚推进裂纹玉佩线索。',
      executionContext: expect.objectContaining({
        source: 'manual',
        source_world_version: 2,
        next_chapter_number: 2,
        goal: '第 2 章标题：第 2 章摘要：林砚推进裂纹玉佩线索。',
        recommended_pov: { character_id: null, name: '第 2 章 POV 建议' },
      }),
    });
  });

  it('generates a serial plan preview and launches one queued goal into Studio review', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);
    vi.mocked(getSerialPlan).mockResolvedValueOnce({
      world_id: 7,
      world_version: 2,
      approved_chapter_count: 1,
      queue: [
        {
          chapter_number: 2,
          title: '第 2 章标题',
          goal: '第 2 章标题：第 2 章摘要：林砚推进裂纹玉佩线索。 核心冲突：第 2 章核心冲突详情 建议 POV：第 2 章 POV 建议',
          summary: '第 2 章摘要：林砚推进裂纹玉佩线索。',
          core_conflict: '第 2 章核心冲突详情',
          pov_suggestion: '第 2 章 POV 建议',
          foreshadow_hints: ['裂纹玉佩'],
          source: 'story_arc',
        },
      ],
      safety_notes: [
        '这是多章目标队列预览，不会一次性生成正文。',
        '每章仍需单独进入 Studio 创建草稿、审稿并由用户确认。',
        '世界进度和 EventLog 只会在章节写入正史后更新。',
      ],
      review_guardrails: [
        '连载队列只是只读计划，不会批量创建章节或正文。',
        '点击单章目标只会进入 Studio 草稿流程；写入正史前必须由用户审稿确认。',
        '未写入正史的队列目标不会更新 canon、EventLog、伏笔状态或世界进度。',
      ],
      convergence_guidance: {
        mode: 'pressure',
        mode_label: '继续加压',
        open_foreshadow_count: 2,
        high_pressure_count: 1,
        stale_count: 0,
        overdue_count: 0,
        priority_foreshadows: [
          {
            foreshadow_id: 5,
            title: '血月密约',
            status: 'advanced',
            urgency_level: 5,
            pressure_level: 'high',
            pressure_reasons: ['高紧迫度：5'],
          },
        ],
        recommendation: '存在高压或久未推进伏笔；后续章节应至少推进一个既有悬念/伏笔。',
        guidance_notes: [
          '收束提示来自现有悬念/伏笔账本，只用于规划目标队列。',
          '这些提示不会写入正史、不会关闭伏笔，也不会推进世界进度。',
        ],
      },
    });

    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);
    await openWriteTab(user);
    await user.click(await screen.findByRole('button', { name: '生成连载队列' }));

    expect(getSerialPlan).toHaveBeenCalledWith(7, 3);
    expect(await screen.findByText('这是多章目标队列预览，不会一次性生成正文。')).toBeInTheDocument();
    expect(screen.getByText('世界进度和 EventLog 只会在章节写入正史后更新。')).toBeInTheDocument();
    expect(screen.getByText('连载队列只是只读计划，不会批量创建章节或正文。')).toBeInTheDocument();
    expect(screen.getByText('点击单章目标只会进入 Studio 草稿流程；写入正史前必须由用户审稿确认。')).toBeInTheDocument();
    expect(screen.getByText('未写入正史的队列目标不会更新 canon、EventLog、伏笔状态或世界进度。')).toBeInTheDocument();
    expect(screen.getByText('继续加压')).toBeInTheDocument();
    expect(screen.getByText('存在高压或久未推进伏笔；后续章节应至少推进一个既有悬念/伏笔。')).toBeInTheDocument();
    expect(screen.getByText('血月密约 · 紧迫度 5 · 高紧迫度：5')).toBeInTheDocument();
    expect(screen.getByText('这些提示不会写入正史、不会关闭伏笔，也不会推进世界进度。')).toBeInTheDocument();
    expect(screen.getByText('第 2 章标题：第 2 章摘要：林砚推进裂纹玉佩线索。 核心冲突：第 2 章核心冲突详情 建议 POV：第 2 章 POV 建议')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '用此目标进入 Studio' }));

    expect(onEnterStudio).toHaveBeenCalledWith(storyArcWorld, {
      initialChapterGoal: '第 2 章标题：第 2 章摘要：林砚推进裂纹玉佩线索。 核心冲突：第 2 章核心冲突详情 建议 POV：第 2 章 POV 建议',
      executionContext: expect.objectContaining({
        source: 'manual',
        source_world_version: 2,
        next_chapter_number: 2,
        source_signals: ['serial_plan_preview', 'story_arc', 'serial_plan_convergence_guidance'],
        recommended_pov: { character_id: null, name: '第 2 章 POV 建议' },
        priority_foreshadows: [expect.objectContaining({
          foreshadow_id: 5,
          title: '血月密约',
          urgency_level: 5,
          reason: '高紧迫度：5',
        })],
        progression_hints: [
          expect.objectContaining({
            hint_type: 'foreshadow',
            title: '连载队列伏笔提示',
            suggested_next_beat: '在 Studio 草稿中推进或回应这些既有悬念/伏笔；是否写入正史仍由用户审核决定。',
          }),
          expect.objectContaining({
            hint_type: 'plot',
            priority: 'high',
            title: '自动连载叙事收束提示',
            rationale: '继续加压：存在高压或久未推进伏笔；后续章节应至少推进一个既有悬念/伏笔。',
            related_foreshadow_ids: [5],
          }),
        ],
        continuity_warnings: [
          expect.objectContaining({
            severity: 'info',
            category: 'serial_plan_review_boundary',
            message: '连载队列只是只读计划，不会批量创建章节或正文。',
          }),
          expect.objectContaining({
            severity: 'info',
            category: 'serial_plan_review_boundary',
            message: '点击单章目标只会进入 Studio 草稿流程；写入正史前必须由用户审稿确认。',
          }),
          expect.objectContaining({
            severity: 'info',
            category: 'serial_plan_review_boundary',
            message: '未写入正史的队列目标不会更新 canon、EventLog、伏笔状态或世界进度。',
          }),
        ],
      }),
    });
  });

  it('renders ten story arc chapters as a dense collapsed index by default', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);
    await openWriteTab(user);

    expect(await screen.findByText('前 10 章故事弧线')).toBeInTheDocument();
    const chapterButtons = screen.getAllByRole('button', { name: /第 \d+ 章 · 第 \d+ 章标题/ });
    expect(chapterButtons).toHaveLength(10);
    expect(chapterButtons[0]).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByRole('button', { name: '第 1 章 · 第 1 章标题 · 2 条伏笔' })).toBeInTheDocument();
    expect(screen.queryByText('第 1 章摘要：林砚推进裂纹玉佩线索。')).not.toBeInTheDocument();
    expect(screen.queryByText('第 1 章核心冲突详情')).not.toBeInTheDocument();
    expect(screen.queryByText('第 1 章 POV 建议')).not.toBeInTheDocument();
  });

  it('expands an individual story arc chapter to reveal full content', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);
    await openWriteTab(user);

    const expandButton = await screen.findByRole('button', { name: '第 1 章 · 第 1 章标题 · 2 条伏笔' });
    expect(expandButton).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('核心冲突')).not.toBeInTheDocument();

    await user.click(expandButton);

    expect(screen.getByRole('button', { name: '第 1 章 · 第 1 章标题 · 2 条伏笔' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('第 1 章摘要：林砚推进裂纹玉佩线索。')).toBeInTheDocument();
    expect(screen.getByText('核心冲突')).toBeInTheDocument();
    expect(screen.getByText('第 1 章核心冲突详情')).toBeInTheDocument();
    expect(screen.getByText('第 1 章 POV 建议')).toBeInTheDocument();
    expect(screen.getByText('裂纹玉佩、雨巷铜铃')).toBeInTheDocument();
  });

  it('allows neighboring story arc chapters to stay readable when both sides are expanded', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);
    await openWriteTab(user);

    await user.click(await screen.findByRole('button', { name: '第 1 章 · 第 1 章标题 · 2 条伏笔' }));
    expect(screen.getByText('第 1 章摘要：林砚推进裂纹玉佩线索。')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '第 2 章 · 第 2 章标题' }));

    expect(screen.getByRole('button', { name: '第 1 章 · 第 1 章标题 · 2 条伏笔' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('button', { name: '第 2 章 · 第 2 章标题' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('第 1 章摘要：林砚推进裂纹玉佩线索。')).toBeInTheDocument();
    expect(screen.getByText('第 1 章核心冲突详情')).toBeInTheDocument();
    expect(screen.getAllByText('第 2 章摘要：林砚推进裂纹玉佩线索。').length).toBeGreaterThan(0);
    expect(screen.getAllByText('第 2 章核心冲突详情').length).toBeGreaterThan(0);
  });

  it('uses top-level tabs instead of quick navigation anchors for major narrative modules', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByRole('button', { name: '世界概览' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '继续创作' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '角色' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '关系' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '伏笔' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '运营分析' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '归档导出' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: '故事弧线' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: '叙事控制台' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: '导出/快照' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '继续创作' }));
    expect(await screen.findByText('前 10 章故事弧线')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '运营分析' }));
    expect(await screen.findByText('故事运营分析')).toBeInTheDocument();
    expect(await screen.findByText('世界近况')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '归档导出' }));
    expect(await screen.findByText('档案与导出')).toBeInTheDocument();
    expect(await screen.findByText('世界档案')).toBeInTheDocument();
  });
});

describe('WorldPage 叙事运营台', () => {
  it('keeps 叙事运营台 read-only for archived worlds', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([
        { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
      ])
      .mockResolvedValueOnce(archivedWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '打开 青岚城' }));

    expect(await screen.findByText('已归档：写作已暂停')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '继续创作' }));
    expect(screen.getByText('下一章准备台')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '用作下一章目标' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '进入创作台并使用此目标' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '归档导出' }));
    expect(screen.getByText('已归档小说为只读模式；可继续导出档案和查看历史快照，恢复写作后才能创建新快照。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '创建世界快照' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '导出世界档案' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '加载快照列表' })).toBeInTheDocument();
  });

  it('loads and displays narrative panels across the split tabs', async () => {
    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('世界正史档案')).toBeInTheDocument();
    expect(getChapterHistory).not.toHaveBeenCalled();
    expect(getNextChapterPrep).not.toHaveBeenCalled();
    expect(getNarrativeHealth).not.toHaveBeenCalled();
    expect(getOpenThreads).not.toHaveBeenCalled();
    expect(getWorldPulse).not.toHaveBeenCalled();
    expect(getArcPlan).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: '运营分析' }));
    await waitFor(() => expect(getWorldPulse).toHaveBeenCalledWith(7));
    expect(getArcPlan).toHaveBeenCalledWith(7);
    expect(getNarrativeHealth).toHaveBeenCalledWith(7);
    expect(getOpenThreads).toHaveBeenCalledWith(7);
    expect(getNextChapterPrep).not.toHaveBeenCalled();
    expect(getChapterHistory).not.toHaveBeenCalled();
    expect(await screen.findByText('故事运营分析')).toBeInTheDocument();
    expect(await screen.findByText('世界近况')).toBeInTheDocument();
    expect(await screen.findByText('篇章规划与收束计划')).toBeInTheDocument();
    expect(await screen.findByText('叙事健康度')).toBeInTheDocument();
    expect(await screen.findByText('开放线索看板')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '继续创作' }));
    await waitFor(() => expect(getNextChapterPrep).toHaveBeenCalledWith(7));
    expect(getChapterHistory).not.toHaveBeenCalled();
    expect(await screen.findByText('下一章准备台')).toBeInTheDocument();
    expect(screen.getByText('林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '用作下一章目标' }));
    expect(screen.getByText('已设为下一章目标：林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '归档导出' }));
    await waitFor(() => expect(getChapterHistory).toHaveBeenCalledWith(7));
    expect((await screen.findAllByText('章节历史')).length).toBeGreaterThan(0);
    expect(screen.getByText('第一章 雨巷密谈 · v1 · 世界 1 → 2')).toBeInTheDocument();
    expect(await screen.findByText('世界历史记录')).toBeInTheDocument();
    expect(getWorldEvents).toHaveBeenCalledWith(7, { limit: 20 });
    expect(await screen.findByText('全局搜索')).toBeInTheDocument();
    expect(await screen.findByText('标签与收藏')).toBeInTheDocument();
    await waitFor(() => expect(listWorldTags).toHaveBeenCalledTimes(2));
    expect(listWorldTags).toHaveBeenCalledWith(7);
    await user.type(screen.getByLabelText('搜索世界资料'), '灯塔');
    await user.click(screen.getByRole('button', { name: '搜索' }));
    expect(await screen.findByText('搜索结果批量打标')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    expect(await screen.findByLabelText('批量对象 ID')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '加载快照列表' }));
    expect(listWorldSnapshots).toHaveBeenCalledWith(7);
  });

  it('shows degraded messages in the split tabs when panel APIs fail', async () => {
    const user = userEvent.setup();
    vi.mocked(getChapterHistory).mockRejectedValueOnce(new Error('history down'));
    vi.mocked(getNextChapterPrep).mockRejectedValueOnce(new Error('prep down'));

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('世界正史档案')).toBeInTheDocument();
    expect(getChapterHistory).not.toHaveBeenCalled();
    await user.click(await screen.findByRole('button', { name: '归档导出' }));
    await waitFor(() => expect(getChapterHistory).toHaveBeenCalledWith(7));
    expect(await screen.findByText('章节历史暂不可用')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '继续创作' }));
    await waitFor(() => expect(getNextChapterPrep).toHaveBeenCalledWith(7));
    expect(await screen.findByText('下一章准备台暂不可用')).toBeInTheDocument();
  });

  it('keeps World Bible manager tabs read-only for archived worlds', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([
        { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
      ])
      .mockResolvedValueOnce(archivedWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '打开 青岚城' }));
    await user.click(screen.getByRole('button', { name: '角色' }));

    expect(await screen.findByText('已归档小说为只读模式；恢复写作后才能编辑世界资料。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '编辑' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '关系' }));
    expect(await screen.findByText('已归档小说为只读模式；恢复写作后才能编辑世界资料。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '+ 新增关系' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '伏笔' }));
    expect(await screen.findByText('已归档小说为只读模式；恢复写作后才能编辑世界资料。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '+ 新增伏笔' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '放弃伏笔' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '删除' })).not.toBeInTheDocument();
    expect(await screen.findByRole('button', { name: '展开时间线' })).toBeInTheDocument();
  });

  it('renders World Bible Editor manager tabs with governance warning', async () => {
    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('青岚城')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '角色' }));
    expect(screen.getByText('角色管理')).toBeInTheDocument();
    expect(getCharacters).toHaveBeenCalledWith(7);
    expect(screen.getByText('这些编辑会正式写入世界状态，并提升世界版本。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '+ 新增角色' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '关系' }));
    expect(screen.getByText('关系管理')).toBeInTheDocument();
    expect(getRelations).toHaveBeenCalledWith(7);
    expect(screen.getByRole('button', { name: '+ 新增关系' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '伏笔' }));
    expect(screen.getAllByText('伏笔账本').length).toBeGreaterThan(0);
    expect(getForeshadowLedger).toHaveBeenCalledWith(7);
    expect(await screen.findByText('伏笔治理台')).toBeInTheDocument();
    expect(screen.getByText('伏笔治理台')).toBeInTheDocument();
    expect(screen.getByText('总数：1')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '+ 新增伏笔' })).toBeInTheDocument();
  });

  it('passes a selected next chapter goal when entering Studio from the regular button', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    await user.click(await screen.findByRole('button', { name: '继续创作' }));
    await user.click(await screen.findByRole('button', { name: '用作下一章目标' }));
    await user.click(screen.getByRole('button', { name: '世界概览' }));
    await user.click(screen.getByRole('button', { name: '继续下一章' }));

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

    await user.click(await screen.findByRole('button', { name: '继续创作' }));
    await user.click(await screen.findByRole('button', { name: '进入创作台并使用此目标' }));

    expect(onEnterStudio).toHaveBeenCalledWith(world, {
      initialChapterGoal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      executionContext: expect.objectContaining({
        source: 'next_chapter_prep',
        recommended_pov: { character_id: 1, name: '林砚' },
      }),
    });
  });
});
