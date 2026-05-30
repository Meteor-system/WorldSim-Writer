import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createChapter, generateCharacterArcReport, writeChapter } from '../api/client';
import type { ChapterExecutionContext, DraftResponse, WorldOverview } from '../api/types';
import { StudioPage } from './StudioPage';

const executionContext: ChapterExecutionContext = {
  source: 'next_chapter_prep',
  source_world_version: 2,
  next_chapter_number: 2,
  goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
  recommended_pov: { character_id: 1, name: '林砚' },
  source_signals: ['character_arc_progression_hint'],
  priority_characters: [{ character_id: 1, name: '林砚', role_type: 'protagonist', status: '开始调查密信', reason: '上一章提示。' }],
  priority_foreshadows: [{ foreshadow_id: 1, title: '裂纹玉佩', status: 'advanced', urgency_level: 4, reason: '该伏笔需要推进。' }],
  progression_hints: [{ hint_type: 'character', priority: 'high', title: '试探沈微霜是否可信', rationale: '上一章已经建立湿信线索。', suggested_next_beat: '林砚带着湿信赴城主府外墙，并设置一次试探。', related_character_ids: [1], related_foreshadow_ids: [1], can_seed_next_chapter_goal: true }],
  continuity_warnings: [{ severity: 'medium', category: 'character_arc', message: '下一章需要补足试探过程。', related_character_ids: [1], related_foreshadow_ids: [] }],
  recent_events: [{ id: 4, event_type: 'chapter_approved', world_version_before: 1, world_version_after: 2, created_at: '2026-05-30T00:00:00Z' }],
};

const draftResponse: DraftResponse = {
  chapter_id: 11,
  draft_id: 101,
  draft_version: 1,
  title: '第一章 雨巷密谈',
  content: '第一段：林砚停在雨巷口。\n\n第二段：沈微霜递来一封湿透的信。',
  context_summary: '林砚与沈微霜交换线索。',
  review_hints: ['确认第二段的信息揭示是否过快'],
  proposed_changes: {
    characters: [{ character_id: 1, status: '开始调查密信', current_goals: ['追查湿信来源'] }],
    foreshadows: [{ foreshadow_id: 1, status: 'advanced', description_note: '湿信推进玉佩线索' }],
  },
  source_world_version: 1,
  change_type: 'generated',
  change_summary: null,
  parent_draft_version: null,
  status: 'reviewing',
  execution_context: executionContext,
};

vi.mock('../api/client', () => ({
  apiRequest: vi.fn(),
  createChapter: vi.fn(async () => ({
    id: 11,
    world_id: 7,
    title: '推进雨巷密谈',
    status: 'drafting',
    draft_version: 1,
    approved_version: null,
    base_world_version: 1,
    approved_content: null,
    chapter_goal: '推进雨巷密谈',
    outline_beats: [],
    outline_context: {},
    critique_report: {},
    execution_context: executionContext,
  })),
  generateOutline: vi.fn(async () => ({
    chapter_id: 11,
    outline_beats: [
      {
        beat_id: 'beat-1',
        summary: '雨巷交换线索',
        pov_character: '林砚',
        location: '雨巷',
        emotional_arc: '警觉 -> 犹疑',
        key_dialogue_hints: ['这封信不该在你手里。'],
      },
    ],
    outline_context: { core_conflict: '林砚判断沈微霜是否可信' },
    status: 'outlined',
  })),
  writeChapter: vi.fn(async () => draftResponse),
  critiqueChapter: vi.fn(),
  generateCriticReport: vi.fn(async () => ({
    chapter_id: 11,
    draft_version: 1,
    current_draft_version: 1,
    is_stale: false,
    overall_score: 78,
    summary: '章节冲突清晰，但第二段信息揭示偏快。',
    dimensions: {
      pacing: { score: 72, summary: '中段推进略快。', issues: [], suggestions: ['放慢第二段的信息揭示。'] },
      tension: { score: 82, summary: '雨巷会面有悬念。', issues: [], suggestions: [] },
      character_consistency: { score: 60, summary: '人物动机需要补强。', issues: [], suggestions: [] },
      dialogue_quality: { score: 68, summary: '对白略直白。', issues: [], suggestions: [] },
      structure: { score: 80, summary: '开端清晰。', issues: [], suggestions: [] },
      world_continuity: { score: 90, summary: '未发现世界观冲突。', issues: [], suggestions: [] },
      readability: { score: 76, summary: '可读性良好。', issues: [], suggestions: [] },
    },
    issues: [
      {
        severity: 'high',
        dimension: 'character_consistency',
        message: '林砚突然信任沈微霜，与当前谨慎状态冲突。',
        paragraph_index: 0,
        suggested_action: '重写相关段落，补足信任建立过程。',
      },
    ],
    suggestions: ['优先修订第一段人物动机。'],
    created_at: '2026-05-29T00:00:00Z',
  })),
  getCriticReport: vi.fn(),
  generateCharacterArcReport: vi.fn(async () => ({
    chapter_id: 11,
    draft_version: 1,
    current_draft_version: 1,
    is_stale: false,
    summary: '本章推动林砚从被动等待转向主动追查湿信来源。',
    character_arcs: [
      {
        character_id: 1,
        name: '林砚',
        role_type: 'protagonist',
        current_status: 'active',
        current_goals: [],
        presence_level: 'major',
        arc_stage: 'choice',
        chapter_function: '在雨巷会面中承担调查者与选择者功能。',
        observed_shift: '从谨慎观察转向主动追问湿信来源。',
        proposed_state_change: { status: '开始调查密信', current_goals: ['追查湿信来源'] },
        continuity_risk: 'medium',
        risk_reason: '如果立刻信任沈微霜，需要补足信任建立过程。',
        suggested_revision: '增加林砚犹疑和试探沈微霜的动作。',
        next_chapter_setup: '让林砚以湿信为线索试探城主府密道。',
      },
    ],
    relationship_notes: [],
    progression_hints: [
      {
        hint_type: 'character',
        priority: 'high',
        title: '让林砚做出是否相信沈微霜的选择',
        rationale: '本章已经建立湿信线索。',
        suggested_next_beat: '林砚带着湿信赴城主府外墙，并设置一次试探。',
        related_character_ids: [1],
        related_foreshadow_ids: [1],
        can_seed_next_chapter_goal: true,
      },
    ],
    created_at: '2026-05-29T00:00:00Z',
  })),
  getCharacterArcReport: vi.fn(),
  suggestGoal: vi.fn(),
  stashDraft: vi.fn(async () => ({ ...draftResponse, draft_version: 2, change_type: 'stash', change_summary: '暂存当前草稿', parent_draft_version: 1 })),
  reviseParagraph: vi.fn(async () => ({
    ...draftResponse,
    draft_version: 2,
    content: '第一段：林砚停在雨巷口，玉佩微微发烫。\n\n第二段：沈微霜递来一封湿透的信。',
    change_type: 'paragraph_rewrite',
    change_summary: '重写第 1 段',
    parent_draft_version: 1,
  })),
  getDraftDiff: vi.fn(async () => ({
    chapter_id: 11,
    from_version: 1,
    to_version: 2,
    from_content: draftResponse.content,
    to_content: '第一段：林砚停在雨巷口，玉佩微微发烫。\n\n第二段：沈微霜递来一封湿透的信。',
    diff_lines: [
      { type: 'removed', text: '第一段：林砚停在雨巷口。' },
      { type: 'added', text: '第一段：林砚停在雨巷口，玉佩微微发烫。' },
    ],
  })),
  getApprovalPreview: vi.fn(async () => ({
    chapter_id: 11,
    draft_version: 1,
    source_world_version: 1,
    current_world_version: 1,
    will_increment_world_version: true,
    world_version_before: 1,
    world_version_after: 2,
    version_conflict: false,
    warnings: [],
    character_changes: [
      { character_id: 1, name: '林砚', before: { status: 'active' }, after: { status: '开始调查密信', current_goals: ['追查湿信来源'] } },
    ],
    foreshadow_changes: [
      { foreshadow_id: 1, title: '裂纹玉佩', before: { status: 'planted' }, after: { status: 'advanced', description: '审核备注：湿信推进玉佩线索' } },
    ],
  })),
}));

const world: WorldOverview = {
  id: 7,
  title: '青岚城',
  genre_template: 'xianxia',
  truth_canon: '灵脉正在衰退。',
  truth_canon_version: 1,
  world_version: 1,
  status: 'running',
  tone_profile: {},
  current_characters: [],
  current_foreshadows: [],
  current_relations: [],
  characters: [{ id: 1, name: '林砚', role_type: 'protagonist', status: 'active', public_profile: {}, hidden_traits: {}, destiny_flag: null, current_goals: [] }],
  relations: [],
  foreshadows: [{ id: 1, source_chapter_id: null, title: '裂纹玉佩', description: '玉佩出现裂纹。', foreshadow_type: 'item', status: 'planted', urgency_level: 4, related_character_ids: [1], expected_resolution_window: null }],
  recent_events: [],
  story_arc: [],
  approved_chapter_count: 0,
};

afterEach(() => {
  cleanup();
  vi.mocked(writeChapter).mockClear();
});

describe('StudioPage Review Studio 2.0 controls', () => {
  it('initializes the chapter goal from initialChapterGoal and keeps it editable', async () => {
    const user = userEvent.setup();
    render(
      <StudioPage
        world={{ ...world, story_arc: [{ chapter_number: 1, title: '备用大纲', summary: '不应覆盖初始目标', core_conflict: '冲突', pov_suggestion: '林砚', foreshadow_hints: [] }] }}
        launchContext={{ initialChapterGoal: '林砚带着湿信赴城主府外墙，并设置一次试探。', executionContext }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    const goal = screen.getByLabelText('章节目标');
    expect(goal).toHaveValue('林砚带着湿信赴城主府外墙，并设置一次试探。');
    expect(goal).not.toHaveValue('不应覆盖初始目标');

    await user.clear(goal);
    await user.type(goal, '用户修改后的下一章目标');
    expect(goal).toHaveValue('用户修改后的下一章目标');
  });

  it('shows launch execution context summary and submits edited context when creating chapter', async () => {
    const user = userEvent.setup();
    render(<StudioPage world={world} launchContext={{ initialChapterGoal: executionContext.goal, executionContext }} onBack={vi.fn()} onApproved={vi.fn()} />);

    expect(screen.getByText('本章执行上下文')).toBeInTheDocument();
    expect(screen.getByText('来源：下一章准备台')).toBeInTheDocument();
    expect(screen.getByText('推荐 POV：林砚')).toBeInTheDocument();
    expect(screen.getByText('优先角色：林砚')).toBeInTheDocument();
    expect(screen.getByText('优先伏笔：裂纹玉佩')).toBeInTheDocument();

    const goal = screen.getByLabelText('章节目标');
    await user.clear(goal);
    await user.type(goal, '用户编辑后的执行目标');
    await user.click(screen.getByRole('button', { name: '创建章节' }));

    expect(createChapter).toHaveBeenCalledWith(7, expect.objectContaining({
      chapter_goal: '用户编辑后的执行目标',
      execution_context: expect.objectContaining({
        source: 'next_chapter_prep',
        goal: '用户编辑后的执行目标',
        recommended_pov: { character_id: 1, name: '林砚' },
      }),
    }));
    expect(await screen.findByText('已冻结执行上下文：next_chapter_prep · v2')).toBeInTheDocument();
  });

  it('creates manual context when Studio opens without NCC execution context', async () => {
    const user = userEvent.setup();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    expect(screen.getByText('本章暂无 NCC 执行上下文。创建章节时会根据当前目标生成手动上下文快照。')).toBeInTheDocument();
    await user.type(screen.getByLabelText('章节目标'), '手动输入章节目标');
    await user.click(screen.getByRole('button', { name: '创建章节' }));

    expect(createChapter).toHaveBeenCalledWith(7, expect.objectContaining({
      execution_context: expect.objectContaining({
        source: 'manual',
        goal: '手动输入章节目标',
        source_signals: ['manual'],
      }),
    }));
  });

  it('shows frozen execution context snapshot after drafting', async () => {
    const user = userEvent.setup();
    render(<StudioPage world={world} launchContext={{ initialChapterGoal: executionContext.goal, executionContext }} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

    expect(await screen.findByText('执行上下文快照')).toBeInTheDocument();
    expect(screen.getByText('目标：林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
    expect(screen.getByText('连续性提醒：下一章需要补足试探过程。')).toBeInTheDocument();
  });

  it('renders version selector, stash, paragraph controls, diff, and approval preview after drafting', async () => {
    const user = userEvent.setup();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

    expect(await screen.findByLabelText('草稿版本')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '暂存当前草稿' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: '重写本段' })[0]).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: '润色本段' })[0]).toBeInTheDocument();
    expect(screen.getByText('版本差异')).toBeInTheDocument();
    expect(screen.getByText('通过后将提交')).toBeInTheDocument();
    expect(screen.getByText('世界版本：1 → 2')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '生成 Critic 报告' }));
    expect(await screen.findByText('总评分：78/100')).toBeInTheDocument();
    expect(screen.getByText('Critic 发现高风险问题，建议修订后再批准。')).toBeInTheDocument();
    expect(screen.getByText('林砚突然信任沈微霜，与当前谨慎状态冲突。')).toBeInTheDocument();
  });

  it('falls back to the chapter draft version label and shows full paragraph card text', async () => {
    const user = userEvent.setup();
    const longParagraph = '第一段：林砚停在雨巷口，掌心的玉佩微微发烫，他反复想起师门旧案与城主府密道之间那些尚未被证实却越来越危险的联系。';
    vi.mocked(writeChapter).mockResolvedValueOnce({
      ...draftResponse,
      draft_version: undefined as unknown as number,
      content: `${longParagraph}\n\n第二段：沈微霜递来一封湿透的信。`,
    });

    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

    expect(await screen.findByRole('option', { name: 'v1' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'v' })).not.toBeInTheDocument();
    expect(screen.getByText(`第 1 段：${longParagraph}`)).toBeInTheDocument();
  });

  it('generates and displays a character arc report from the draft review flow', async () => {
    const user = userEvent.setup();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(screen.getByRole('button', { name: '生成角色弧线报告' }));

    expect(generateCharacterArcReport).toHaveBeenCalledWith(11);
    expect(await screen.findByText('角色弧线报告')).toBeInTheDocument();
    expect(screen.getByText('本章推动林砚从被动等待转向主动追查湿信来源。')).toBeInTheDocument();
    expect(screen.getByText('林砚 · protagonist')).toBeInTheDocument();
    expect(screen.getByText('让林砚做出是否相信沈微霜的选择')).toBeInTheDocument();
  });
});
