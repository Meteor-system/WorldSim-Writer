import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiRequest, assignWorldTag, bulkAssignWorldTag, compareWorldSnapshots, confirmWorldImport, createSampleWorld, createWorld, createWorldFromSeed, createWorldSnapshot, createWorldTag, deleteWorldTag, exportWorldArchiveMarkdown, generateStoryArc, getArcPlan, getChapterHistory, getChapterHistoryDetail, getCharacters, getForeshadowLedger, getNarrativeHealth, getNextChapterPrep, getOpenThreads, getRelations, getWorldEvents, getWorldPulse, getWorldSeed, getWorldTag, listWorldImports, listWorldSeeds, listWorldSnapshots, listWorldTags, mergeWorldTag, previewWorldImport, searchWorld, unassignWorldTag, updateWorldStatus, updateWorldTag } from '../api/client';
import type { WorldOverview, WorldSearchResponse } from '../api/types';
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
  getWorldTag: vi.fn(),
  listWorldImports: vi.fn(),
  listWorldSeeds: vi.fn(),
  listWorldTags: vi.fn(),
  mergeWorldTag: vi.fn(),
  previewWorldImport: vi.fn(),
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
  vi.mocked(exportWorldArchiveMarkdown).mockReset();
  vi.mocked(generateStoryArc).mockReset();
  vi.mocked(getChapterHistory).mockReset();
  vi.mocked(getChapterHistoryDetail).mockReset();
  vi.mocked(getNextChapterPrep).mockReset();
  vi.mocked(getNarrativeHealth).mockReset();
  vi.mocked(getOpenThreads).mockReset();
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
  vi.mocked(listWorldImports).mockResolvedValue({ world_id: 7, batches: [] });
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
    expect(screen.getByText('今日运营')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('WORLD CANON');
    expect(document.body).not.toHaveTextContent('World Canon');
    expect(document.body).not.toHaveTextContent('WORLD OPERATIONS');
    expect(document.body).not.toHaveTextContent('World Operations');
    expect(document.body).not.toHaveTextContent('xianxia');
    expect(document.body).not.toHaveTextContent('running');
  });

  it('shows world operations metrics in user language', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('世界运营仪表盘'));
    expect(dashboard.getByText('世界运营仪表盘')).toBeInTheDocument();
    expect(dashboard.getByText('世界进度：第 2 版')).toBeInTheDocument();
    expect(dashboard.getByText('已写入正史章节：1')).toBeInTheDocument();
    expect(dashboard.getByText('近期世界历史记录：0')).toBeInTheDocument();
    expect(dashboard.getByText('待处理悬念/伏笔：1')).toBeInTheDocument();
  });

  it('shows candidate material references as safe operations context', async () => {
    vi.mocked(getNextChapterPrep).mockResolvedValueOnce({
      world_id: 7,
      world_version: 2,
      next_chapter_number: 2,
      suggested_goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      recommended_pov_character_id: 1,
      recommended_pov_character_name: '林砚',
      source_signals: ['import_material_reference'],
      priority_characters: [],
      priority_foreshadows: [],
      progression_hints: [],
      continuity_warnings: [],
      recent_events: [],
      material_references: [{ asset_id: 9, batch_id: 12, asset_pool: 'inspiration', title: '雨夜审讯', summary: '雨夜审讯从一盏坏灯开始。', raw_text: '灵感：雨夜审讯从一盏坏灯开始。', source_title: '旧设定.md', source_type: 'pasted_text', created_at: '2026-06-04T00:00:01Z', safety_note: '导入素材参考只用于创作提示，不会自动改写正式 canon。' }],
    });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('世界运营仪表盘'));
    expect(await dashboard.findByText('候选素材参考：1 条')).toBeInTheDocument();
    expect(dashboard.getByText('只作为下一章写作参考，不会自动写入正式设定。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('asset_id');
    expect(document.body).not.toHaveTextContent('batch_id');
    expect(document.body).not.toHaveTextContent('inspiration');
  });

  it('recommends explainable next actions from current world data', async () => {
    const onEnterStudio = vi.fn();
    const user = userEvent.setup();
    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('世界运营仪表盘'));
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

    const dashboard = within(await screen.findByLabelText('世界运营仪表盘'));
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
});

describe('WorldPage world creation', () => {
  it('shows the newcomer three-minute loop and high-tension embryo entry', async () => {
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest).mockResolvedValueOnce([]);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('3 分钟开始运营你的故事世界')).toBeInTheDocument();
    expect(screen.getByText('选世界胚胎')).toBeInTheDocument();
    expect(screen.getByText('生成第一章')).toBeInTheDocument();
    expect(screen.getByText('写入正史')).toBeInTheDocument();
    expect(screen.getByText('查看世界变化')).toBeInTheDocument();
    expect(await screen.findByText('高张力世界胚胎')).toBeInTheDocument();
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
    await user.click(screen.getByRole('button', { name: '直接创建此胚胎' }));

    expect(createWorldFromSeed).toHaveBeenCalledWith('forgotten-sun-city');
    expect(await screen.findByText('青岚城')).toBeInTheDocument();
    expect(screen.queryByText('Writer Draft')).not.toBeInTheDocument();
    expect(screen.queryByText('世界推进结算')).not.toBeInTheDocument();
  });

  it('aligns the first chapter launchpad with the three-minute loop', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('第一章启动台')).toBeInTheDocument();
    expect(screen.getByText('生成第一章 → 写入正史 → 查看世界变化')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('First Chapter Launchpad');
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
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('归档前建议先创建世界快照并导出 Markdown ZIP。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '归档当前小说' })).toBeInTheDocument();
  });

  it('can archive and restore the current world without leaving the page', async () => {
    const user = userEvent.setup();
    vi.mocked(updateWorldStatus)
      .mockResolvedValueOnce({ ...world, status: 'archived' })
      .mockResolvedValueOnce({ ...world, status: 'active' });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

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
    expect(screen.queryByText('第一章启动台')).not.toBeInTheDocument();
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
    expect(await screen.findByText('第一章启动台')).toBeInTheDocument();
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
  it('shows a first chapter launchpad that can generate an arc when no story arc exists', async () => {
    const user = userEvent.setup();
    vi.mocked(generateStoryArc).mockResolvedValueOnce({
      world_id: 7,
      story_arc: storyArcWorld.story_arc,
    });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('第一章启动台')).toBeInTheDocument();
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

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('第一章启动台')).toBeInTheDocument();
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

  it('shows imported references in the first chapter launchpad and carries them into Studio context', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);
    vi.mocked(getNextChapterPrep).mockResolvedValueOnce({
      world_id: 7,
      world_version: 2,
      next_chapter_number: 2,
      suggested_goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      recommended_pov_character_id: 1,
      recommended_pov_character_name: '林砚',
      source_signals: ['import_material_reference'],
      priority_characters: [],
      priority_foreshadows: [],
      progression_hints: [],
      continuity_warnings: [],
      recent_events: [],
      material_references: [
        {
          asset_id: 9,
          batch_id: 3,
          asset_pool: 'inspiration',
          title: '雨夜审讯',
          summary: '雨夜审讯从一盏坏灯开始。',
          raw_text: '灵感：雨夜审讯从一盏坏灯开始。',
          source_title: '旧设定.md',
          source_type: 'markdown',
          created_at: '2026-06-04T00:00:00Z',
          safety_note: '导入素材参考只用于创作提示，不会自动改写正式 canon。',
        },
      ],
    });

    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    expect(await screen.findByText('已准备 1 条候选素材写作参考。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('已准备 1 条导入素材参考。');
    expect(screen.getAllByText('候选素材写作参考').length).toBeGreaterThan(0);
    expect(screen.getAllByText('雨夜审讯（来源：旧设定.md）').length).toBeGreaterThan(0);
    expect(screen.getAllByText('雨夜审讯从一盏坏灯开始。').length).toBeGreaterThan(0);
    expect(screen.getByText('这些候选素材只会随下一章目标进入创作台，不会自动写入正式设定。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('这些素材只会随下一章目标进入创作台，不会自动写入正式设定。');
    expect(document.body).not.toHaveTextContent('正式 canon');
    expect(document.body).not.toHaveTextContent('asset_id');
    expect(document.body).not.toHaveTextContent('batch_id');
    expect(document.body).not.toHaveTextContent('inspiration');

    expect(screen.getByRole('button', { name: '带候选素材参考进入创作台' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '用此目标进入创作台' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '带候选素材参考进入创作台' }));

    expect(onEnterStudio).toHaveBeenCalledWith(storyArcWorld, {
      initialChapterGoal: '第 2 章标题：第 2 章摘要：林砚推进裂纹玉佩线索。',
      executionContext: expect.objectContaining({
        material_references: expect.arrayContaining([expect.objectContaining({ title: '雨夜审讯', source_title: '旧设定.md' })]),
      }),
    });
  });

  it('renders ten story arc chapters as a dense collapsed index by default', async () => {
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

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

  it('renders quick navigation anchors to major narrative modules', async () => {
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('前 10 章故事弧线')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '故事弧线' })).toHaveAttribute('href', '#story-arc-planner');
    expect(screen.getByRole('link', { name: '叙事控制台' })).toHaveAttribute('href', '#narrative-control-center');
    expect(screen.getByRole('link', { name: '导出/快照' })).toHaveAttribute('href', '#world-archive');
    expect(screen.getByRole('link', { name: '章节历史' })).toHaveAttribute('href', '#chapter-history');
    expect(document.querySelector('#story-arc-planner')).toBeInTheDocument();
    expect(document.querySelector('#narrative-control-center')).toBeInTheDocument();
    expect(document.querySelector('#world-archive')).toBeInTheDocument();
    expect(document.querySelector('#chapter-history')).toBeInTheDocument();
  });
});

describe('WorldPage Narrative Control Center', () => {
  it('keeps Narrative Control Center read-only for archived worlds', async () => {
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
    expect(await screen.findByText('Narrative Control Center')).toBeInTheDocument();
    expect(screen.getByText('已归档小说为只读模式；恢复写作后才能把建议带入创作台。')).toBeInTheDocument();
    expect(screen.getByText('下一章准备台')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '用作下一章目标' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '进入创作台并使用此目标' })).not.toBeInTheDocument();
    expect(screen.getByText('已归档小说为只读模式；可继续导出档案和查看历史快照，恢复写作后才能创建新快照。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '创建世界快照' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '导出世界档案' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '加载快照列表' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '恢复写作' })).toBeInTheDocument();
  });

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
    expect((await screen.findAllByText('章节历史')).length).toBeGreaterThan(0);
    expect(screen.getByText('第一章 雨巷密谈 · v1 · 世界 1 → 2')).toBeInTheDocument();
    expect(screen.getByText('下一章准备台')).toBeInTheDocument();
    expect(screen.getByText('林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
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

    await user.click(screen.getByRole('button', { name: '用作下一章目标' }));
    expect(screen.getByText('已设为下一章目标：林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
  });

  it('refreshes next chapter references after confirming imported material', async () => {
    const user = userEvent.setup();
    vi.mocked(getNextChapterPrep)
      .mockResolvedValueOnce({
        world_id: 7,
        world_version: 2,
        next_chapter_number: 2,
        suggested_goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
        recommended_pov_character_id: 1,
        recommended_pov_character_name: '林砚',
        source_signals: [],
        priority_characters: [],
        priority_foreshadows: [],
        progression_hints: [],
        continuity_warnings: [],
        recent_events: [],
        material_references: [],
      })
      .mockResolvedValueOnce({
        world_id: 7,
        world_version: 2,
        next_chapter_number: 2,
        suggested_goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
        recommended_pov_character_id: 1,
        recommended_pov_character_name: '林砚',
        source_signals: ['import_material_reference'],
        priority_characters: [],
        priority_foreshadows: [],
        progression_hints: [],
        continuity_warnings: [],
        recent_events: [],
        material_references: [{ asset_id: 9, batch_id: 12, asset_pool: 'inspiration', title: '雨夜审讯', summary: '雨夜审讯从一盏坏灯开始。', raw_text: '灵感：雨夜审讯从一盏坏灯开始。', source_title: '旧设定.md', source_type: 'pasted_text', created_at: '2026-06-04T00:00:01Z', safety_note: '导入素材参考只用于创作提示，不会自动改写正式 canon。' }],
      });
    vi.mocked(previewWorldImport).mockResolvedValueOnce({
      world_id: 7,
      source_type: 'pasted_text',
      source_title: '粘贴素材',
      cleaned_excerpt: '灵感：雨夜审讯从一盏坏灯开始。',
      asset_counts: { canon: 0, character: 0, inspiration: 1 },
      conflicts: [],
      assets: [{ asset_pool: 'inspiration', title: '雨夜审讯', summary: '雨夜审讯从一盏坏灯开始。', raw_text: '灵感：雨夜审讯从一盏坏灯开始。', metadata: {} }],
    });
    vi.mocked(confirmWorldImport).mockResolvedValueOnce({
      batch: {
        id: 12,
        world_id: 7,
        source_type: 'pasted_text',
        source_title: '粘贴素材',
        original_excerpt: '灵感：雨夜审讯从一盏坏灯开始。',
        cleaned_excerpt: '灵感：雨夜审讯从一盏坏灯开始。',
        status: 'confirmed',
        asset_counts: { canon: 0, character: 0, inspiration: 1 },
        conflicts: [],
        created_at: '2026-06-04T00:00:00Z',
        confirmed_at: '2026-06-04T00:00:01Z',
      },
      assets: [{ id: 9, world_id: 7, batch_id: 12, status: 'candidate', asset_pool: 'inspiration', title: '雨夜审讯', summary: '雨夜审讯从一盏坏灯开始。', raw_text: '灵感：雨夜审讯从一盏坏灯开始。', metadata: {}, created_at: '2026-06-04T00:00:01Z' }],
    });

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await screen.findByText('素材导入节点');
    expect(screen.queryByText('雨夜审讯')).not.toBeInTheDocument();
    await user.type(screen.getByLabelText('素材正文'), '灵感：雨夜审讯从一盏坏灯开始。');
    expect(screen.queryByRole('button', { name: '生成结构化预览' })).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '生成候选素材预览' }));
    await user.click(await screen.findByRole('button', { name: '确认写入候选素材' }));

    expect(await screen.findByText('已写入候选素材。')).toBeInTheDocument();
    await waitFor(() => expect(getNextChapterPrep).toHaveBeenCalledTimes(2));
    expect(await screen.findByText('这些候选素材只是下一章写作参考，不会自动改写正式设定。')).toBeInTheDocument();
    expect(screen.getByText('雨夜审讯（来源：旧设定.md）')).toBeInTheDocument();
  });

  it('shows degraded Narrative Control Center messages when panel APIs fail', async () => {
    vi.mocked(getChapterHistory).mockRejectedValueOnce(new Error('history down'));
    vi.mocked(getNextChapterPrep).mockRejectedValueOnce(new Error('prep down'));

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await waitFor(() => expect(getChapterHistory).toHaveBeenCalledWith(7));
    expect(await screen.findByText('章节历史暂不可用')).toBeInTheDocument();
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
    await user.click(screen.getByRole('button', { name: '角色管理' }));

    expect(await screen.findByText('已归档小说为只读模式；恢复写作后才能编辑世界资料。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '编辑' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '关系管理' }));
    expect(await screen.findByText('已归档小说为只读模式；恢复写作后才能编辑世界资料。')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '+ 新增关系' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '伏笔账本' }));
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

describe('WorldPage motion and layout polish', () => {
  it('renders the overview as a staged responsive workspace without internal identifiers', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    expect(await screen.findByText('世界正史档案')).toBeInTheDocument();

    const workspace = screen.getByTestId('world-overview-workspace');
    expect(workspace).toHaveClass('workspace-shell');
    expect(workspace).toHaveClass('motion-page-enter');

    const primary = screen.getByTestId('world-primary-stage');
    expect(primary).toHaveClass('space-y-8');

    const supporting = screen.getByTestId('world-supporting-rail');
    expect(supporting).toHaveClass('space-y-5');

    expect(document.body).not.toHaveTextContent('WORLD CANON');
    expect(document.body).not.toHaveTextContent('WORLD OPERATIONS');
    expect(document.body).not.toHaveTextContent('xianxia');
    expect(document.body).not.toHaveTextContent('running');
  });

  it('adds motion and hierarchy classes to dashboard cards and actions', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('世界运营仪表盘'));
    expect(dashboard.getByTestId('world-dashboard-metrics')).toHaveClass('gap-4');
    expect(dashboard.getByTestId('world-dashboard-actions')).toHaveClass('lg:grid-cols-3');
    dashboard.getAllByTestId('world-dashboard-action-card').forEach((card) => {
      expect(card).toHaveClass('motion-soft-lift');
      expect(card).toHaveClass('surface-layer');
    });
  });
});
