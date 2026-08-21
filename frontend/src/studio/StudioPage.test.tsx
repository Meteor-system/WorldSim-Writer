import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { abandonChapter, apiRequest, approveChapter, checkApprovalConsistency, createChapter, editDraft, exportWorldArchiveMarkdown, generateCharacterArcReport, generateCriticReport, generateOutline, getApprovalPreview, getApprovalReadiness, getChapterHistory, getChapterHistoryDetail, getDraftVersion, rejectDraft, reviseDraft, reviseParagraph, stashDraft, writeChapter } from '../api/client';
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
  material_references: [],
};

const approvalPanelVersion = vi.hoisted(() => ({ current: 1 }));
const approvalOpeningPovTarget = vi.hoisted(() => ({
  current: {
    required: false,
    locked_character_id: null as number | null,
    locked_character_name: null as string | null,
  },
}));

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

vi.mock('../workbench/ConvergencePanel', () => ({
  ConvergencePanel: () => null,
}));

vi.mock('../api/client', () => ({
  apiRequest: vi.fn(async () => world),
  retrieveWorldMemory: vi.fn(async () => ({ world_id: 7, approved_chapters: 1, query: '', retrieved: [] })),
  getConvergenceRatio: vi.fn(async () => ({ world_id: 7, opened_threads: 0, closed_threads: 0, merged_threads: 0, ratio: 0 })),
  abandonChapter: vi.fn(async () => ({
    id: 11,
    world_id: 7,
    title: '第一章 雨巷密谈',
    status: 'abandoned',
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
  approveChapter: vi.fn(async () => ({ status: 'approved' })),
  exportWorldArchiveMarkdown: vi.fn(async () => ({
    world_id: 7,
    world_version: 2,
    generated_at: '2026-06-02T00:00:00Z',
    archive_filename: 'qinglan-v2.zip',
    archive_format: 'zip',
    archive_encoding: 'base64',
    archive_base64: 'UEs=',
    files_are_inline: true,
    files: [{ path: 'World.md', content: '# 青岚城' }],
  })),
  checkApprovalConsistency: vi.fn(async () => ({
    chapter_id: 11,
    draft_version: 1,
    selected_change_indexes: { characters: [0], foreshadows: [0] },
    consistency_summary: { status: 'needs_review', total: 1, info_count: 0, warning_count: 1, blocking_count: 0 },
    consistency_warnings: [
      { severity: 'warning', category: 'character_jump', message: '角色「林砚」的状态与目标同时大幅变化，请确认正文已有足够铺垫。', object_type: 'character', object_id: 1, change_index: 0, details: {} },
    ],
  })),
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
  editDraft: vi.fn(async () => draftResponse),
  rejectDraft: vi.fn(async () => ({ ...draftResponse, status: 'rejected' })),
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
  reviseDraft: vi.fn(async () => {
    approvalPanelVersion.current = 2;
    return {
      ...draftResponse,
      draft_id: 102,
      draft_version: 2,
      title: '第一章 雨巷密谈（修订版）',
      content: '修订版第一段：林砚没有立刻信任沈微霜，而是先以湿信试探她。\n\n第二段：沈微霜递来一封湿透的信。',
      context_summary: '修订版补足林砚试探过程。',
      review_hints: ['重新生成 Critic 报告确认高风险是否解除'],
      change_type: 'revision',
      change_summary: '补足林砚试探沈微霜的过程',
      parent_draft_version: 1,
    };
  }),
  getDraftVersion: vi.fn(async (_chapterId: number, draftVersion: number) => (
    draftVersion === 1
      ? draftResponse
      : {
          ...draftResponse,
          draft_id: 102,
          draft_version: 2,
          title: '第一章 雨巷密谈（修订版）',
          content: '修订版第一段：林砚没有立刻信任沈微霜，而是先以湿信试探她。\n\n第二段：沈微霜递来一封湿透的信。',
          change_type: 'revision',
          change_summary: '补足林砚试探沈微霜的过程',
          parent_draft_version: 1,
        }
  )),
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
    draft_version: approvalPanelVersion.current,
    opening_pov_confirmation_target: approvalOpeningPovTarget.current,
    source_world_version: 1,
    current_world_version: 1,
    will_increment_world_version: true,
    world_version_before: 1,
    world_version_after: 2,
    version_conflict: false,
    warnings: [],
    consistency_summary: { status: 'needs_review', total: 1, info_count: 0, warning_count: 1, blocking_count: 0 },
    consistency_warnings: [
      { severity: 'warning', category: 'character_jump', message: '角色「林砚」的状态与目标同时大幅变化，请确认正文已有足够铺垫。', object_type: 'character', object_id: 1, change_index: 0, details: {} },
    ],
    character_changes: [
      { change_index: 0, selected_by_default: true, character_id: 1, name: '林砚', before: { status: 'active' }, after: { status: '开始调查密信', current_goals: ['追查湿信来源'] } },
    ],
    foreshadow_changes: [
      { change_index: 0, selected_by_default: true, foreshadow_id: 1, title: '裂纹玉佩', before: { status: 'planted' }, after: { status: 'advanced', description: '审核备注：湿信推进玉佩线索' } },
    ],
  })),
  getChapterHistory: vi.fn(async () => ({
    world_id: 7,
    chapters: [{ id: 11, title: draftResponse.title, status: 'approved', approved_version: 1, base_world_version: 1 }],
  })),
  getChapterHistoryDetail: vi.fn(async () => ({
    id: 11,
    world_id: 7,
    title: draftResponse.title,
    status: 'approved',
    approved_version: 1,
    base_world_version: 1,
    approved_content: draftResponse.content,
    world_version_before: 1,
    world_version_after: 2,
    events: [],
  })),
  getApprovalReadiness: vi.fn(async () => ({
    chapter_id: 11,
    draft_version: approvalPanelVersion.current,
    status: 'needs_review',
    summary: '存在建议复核项，请确认后再批准。',
    world_version: { source_world_version: 1, current_world_version: 1, matches: true },
    checks: [
      { key: 'world_version', label: '世界版本一致', status: 'pass', message: '草稿基于当前世界版本。', details: {} },
      { key: 'critic_high_risk', label: 'Critic 高风险', status: 'warning', message: '尚未生成 Critic 报告。', details: {} },
    ],
    high_risk_items: [],
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

const approvedWorld: WorldOverview = {
  ...world,
  world_version: 2,
  approved_chapter_count: 1,
  recent_events: [
    {
      id: 88,
      world_id: 7,
      chapter_id: 11,
      event_type: 'chapter_approved',
      source_type: 'approval',
      commit_id: 'commit-88',
      payload: { chapter_title: '第一章 雨巷密谈' },
      world_version_before: 1,
      world_version_after: 2,
      created_at: '2026-06-02T00:00:00Z',
    },
  ],
};

function renderResumedStudio(
  resumedDraft: DraftResponse = draftResponse,
  draftVersions: number[] = [resumedDraft.draft_version],
  callbacks: { onBack?: () => void; onAbandoned?: (worldId: number) => void } = {},
) {
  return render(
    <StudioPage
      world={world}
      launchContext={{
        resumeSession: {
          chapter: {
            id: resumedDraft.chapter_id,
            world_id: 7,
            title: resumedDraft.title,
            status: 'reviewing',
            draft_version: resumedDraft.draft_version,
            approved_version: null,
            base_world_version: 1,
            approved_content: null,
            chapter_goal: '推进雨巷密谈',
            outline_beats: [],
            outline_context: {},
            critique_report: {},
            execution_context: executionContext,
          },
          draft: resumedDraft,
          draft_versions: draftVersions,
        },
      }}
      onBack={callbacks.onBack ?? vi.fn()}
      onApproved={vi.fn()}
      onAbandoned={callbacks.onAbandoned}
    />,
  );
}

const openingPovExecutionContext: ChapterExecutionContext = {
  ...executionContext,
  next_chapter_number: 1,
};

function openingPovDraft(draftVersion = 1): DraftResponse {
  return {
    ...draftResponse,
    draft_id: draftVersion === 1 ? 101 : 102,
    draft_version: draftVersion,
    title: draftVersion === 1 ? '第一章 雨巷密谈' : '第一章 雨巷密谈（修订版）',
    content: draftVersion === 1
      ? draftResponse.content
      : '修订版第一段：林砚在雨巷口审视湿信，没有越过自己的所知。\n\n第二段：沈微霜递来一封湿透的信。',
    change_type: draftVersion === 1 ? 'generated' : 'revision',
    change_summary: draftVersion === 1 ? null : '补足林砚限知视角',
    parent_draft_version: draftVersion === 1 ? null : 1,
    execution_context: openingPovExecutionContext,
    outline_context: {
      opening_contract: {
        locked_pov: '林砚限知第三人称。',
      },
    },
    quality_report: {
      profile: 'opening_chapter',
      status: 'pass',
      validation_version: 5,
      evaluated_draft_version: draftVersion,
      current_draft_version: draftVersion,
      checks: [
        { label: '背景建立', status: 'pass' },
        { label: '稳定 POV', status: 'pass' },
      ],
    },
  };
}

function renderResumedOpeningPovStudio(
  resumedDraft: DraftResponse = openingPovDraft(),
  draftVersions: number[] = [resumedDraft.draft_version],
) {
  approvalOpeningPovTarget.current = {
    required: true,
    locked_character_id: 1,
    locked_character_name: '林砚',
  };
  return render(
    <StudioPage
      world={world}
      launchContext={{
        resumeSession: {
          chapter: {
            id: resumedDraft.chapter_id,
            world_id: 7,
            title: resumedDraft.title,
            status: 'reviewing',
            draft_version: resumedDraft.draft_version,
            approved_version: null,
            base_world_version: 1,
            approved_content: null,
            chapter_goal: '推进雨巷密谈',
            outline_beats: [],
            outline_context: resumedDraft.outline_context ?? {},
            critique_report: {},
            execution_context: openingPovExecutionContext,
          },
          draft: resumedDraft,
          draft_versions: draftVersions,
        },
      }}
      onBack={vi.fn()}
      onApproved={vi.fn()}
    />,
  );
}

afterEach(() => {
  cleanup();
  approvalPanelVersion.current = 1;
  approvalOpeningPovTarget.current = {
    required: false,
    locked_character_id: null,
    locked_character_name: null,
  };
  vi.mocked(apiRequest).mockClear();
  vi.mocked(abandonChapter).mockReset();
  vi.mocked(abandonChapter).mockResolvedValue({
    id: 11,
    world_id: 7,
    title: '第一章 雨巷密谈',
    status: 'abandoned',
    draft_version: 1,
    approved_version: null,
    base_world_version: 1,
    approved_content: null,
    chapter_goal: '推进雨巷密谈',
    outline_beats: [],
    outline_context: {},
    critique_report: {},
    execution_context: executionContext,
  });
  vi.mocked(approveChapter).mockClear();
  vi.mocked(checkApprovalConsistency).mockClear();
  vi.mocked(createChapter).mockClear();
  vi.mocked(exportWorldArchiveMarkdown).mockClear();
  vi.mocked(writeChapter).mockClear();
  vi.mocked(generateOutline).mockClear();
  vi.mocked(getApprovalPreview).mockClear();
  vi.mocked(generateCriticReport).mockClear();
  vi.mocked(generateCharacterArcReport).mockClear();
  vi.mocked(getApprovalReadiness).mockClear();
  vi.mocked(getChapterHistory).mockClear();
  vi.mocked(getChapterHistoryDetail).mockClear();
  vi.mocked(editDraft).mockClear();
  vi.mocked(rejectDraft).mockClear();
  vi.mocked(stashDraft).mockClear();
  vi.mocked(reviseDraft).mockClear();
  vi.mocked(reviseParagraph).mockClear();
  vi.mocked(getDraftVersion).mockClear();
});

describe('StudioPage Review Studio 2.0 controls', () => {
  it('renders the opening-chapter quality review in the three-column studio landmarks', () => {
    const resumedDraft = {
      ...draftResponse,
      quality_report: {
        opening_chapter: {
          checks: [
            { label: '背景建立', passed: true },
            { label: '主角身份与动机', passed: true },
            { label: '性格选择', passed: true },
            { label: '冲突目标', passed: true },
            { label: '稳定 POV', passed: true },
            { label: '悬念钩子', passed: true },
          ],
        },
      },
    } as DraftResponse;

    renderResumedStudio(resumedDraft);

    expect(screen.getByRole('region', { name: '世界与章节导航' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: '大纲与正文编辑' })).toBeInTheDocument();
    const approvalRegion = screen.getByRole('region', { name: '质量与 Canon 审批' });
    expect(approvalRegion).toBeInTheDocument();
    expect(screen.getByText('首章质量')).toBeInTheDocument();
    expect(screen.getByText('背景建立')).toBeInTheDocument();
    expect(screen.getByText('主角身份与动机')).toBeInTheDocument();
    expect(screen.getByText('性格选择')).toBeInTheDocument();
    expect(screen.getByText('冲突目标')).toBeInTheDocument();
    expect(screen.getByText('稳定 POV')).toBeInTheDocument();
    expect(approvalRegion).toContainElement(screen.getByRole('button', { name: '写入正史并更新世界' }));
  });

  it('shows the chapter memory card on the draft stage', () => {
    renderResumedStudio({
      ...draftResponse,
      memory_card: {
        facts: ['林砚拿到湿信'],
        emotional_arc: '警觉 -> 犹疑',
        causal_links: ['湿信指向城主府'],
        characters_present: [1],
      },
    });

    expect(screen.getByRole('region', { name: '本章记忆卡' })).toHaveTextContent('林砚拿到湿信');
    expect(screen.getByText('情绪弧：警觉 -> 犹疑')).toBeInTheDocument();
  });

  it('shows non-blocking missing and weak advisories, terminology samples, and corrected check paragraphs', () => {
    const resumedDraft = {
      ...openingPovDraft(),
      quality_report: {
        ...openingPovDraft().quality_report,
        checks: [
          { label: '背景建立', status: 'pass', paragraph_index: 0, corrected_index: 1, quote: '雨巷口' },
        ],
        advisories: [
          { check: 'inciting_incident', label: '触发事件', state: 'missing', message: 'opening contract 未提供触发事件。', blocking: false },
          { check: 'jargon_density', label: '术语密度', state: 'weak', message: '专有名词首次出现时缺少就地解释。', blocking: false, term_count: 2, unglossed_terms: ['灵脉', '城主府'] },
        ],
      },
    } as DraftResponse;

    renderResumedStudio(resumedDraft);

    const advisorySection = screen.getByRole('region', { name: '非阻断建议' });
    expect(advisorySection).toHaveTextContent('触发事件');
    expect(advisorySection).toHaveTextContent('状态：missing');
    expect(advisorySection).toHaveTextContent('术语密度');
    expect(advisorySection).toHaveTextContent('状态：weak');
    expect(advisorySection).toHaveTextContent('术语样本：灵脉、城主府');
    expect(screen.getByText('自动校正：第 2 段')).toBeInTheDocument();
  });

  it('requires an explicit locked-POV confirmation before a resumed passing opening draft can be approved', async () => {
    const user = userEvent.setup();
    renderResumedOpeningPovStudio();

    const approvalRegion = screen.getByRole('region', { name: '质量与 Canon 审批' });
    expect(await within(approvalRegion).findByText('本章锁定 POV：林砚')).toBeInTheDocument();
    expect(within(approvalRegion).getByText('当前草稿版本：v1')).toBeInTheDocument();
    const confirmation = within(approvalRegion).getByRole('checkbox', {
      name: '我确认本章锁定 POV：林砚（限知第三人称），并以当前草稿版本 v1 写入正史',
    });
    expect(confirmation).not.toBeChecked();

    const approveButton = within(approvalRegion).getByRole('button', { name: '写入正史并更新世界' });
    expect(approveButton).toBeDisabled();
    await user.click(approveButton);

    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('fail-closes approval when a required opening-POV target cannot be resolved', async () => {
    approvalOpeningPovTarget.current = {
      required: true,
      locked_character_id: null,
      locked_character_name: null,
    };
    renderResumedStudio(openingPovDraft());

    expect(await screen.findByRole('alert')).toHaveTextContent('首章 POV 确认目标无效或与当前章节/草稿版本不匹配');
    const approveButton = screen.getByRole('button', { name: '写入正史并更新世界' });
    expect(approveButton).toBeDisabled();
    await userEvent.setup().click(approveButton);
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('fail-closes approval without throwing when the opening-POV target required flag has an invalid runtime type', async () => {
    approvalOpeningPovTarget.current = {
      required: 'true',
      locked_character_id: 1,
      locked_character_name: '林砚',
    } as never;
    renderResumedStudio(openingPovDraft());

    expect(await screen.findByRole('alert')).toHaveTextContent('首章 POV 确认目标无效或与当前章节/草稿版本不匹配');
    const approveButton = screen.getByRole('button', { name: '写入正史并更新世界' });
    expect(approveButton).toBeDisabled();
    await userEvent.setup().click(approveButton);
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('does not let non-blocking advisories prevent approval after the required POV confirmation', async () => {
    const user = userEvent.setup();
    const resumedDraft = openingPovDraft();
    resumedDraft.quality_report = {
      ...resumedDraft.quality_report,
      advisories: [
        { check: 'inciting_incident', label: '触发事件', state: 'weak', message: '建议明确触发事件。', blocking: false },
      ],
    };
    renderResumedOpeningPovStudio(resumedDraft);

    const confirmation = await screen.findByRole('checkbox', {
      name: '我确认本章锁定 POV：林砚（限知第三人称），并以当前草稿版本 v1 写入正史',
    });
    await user.click(confirmation);
    await waitFor(() => expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));

    expect(approveChapter).toHaveBeenCalledWith(11, {
      draft_version: 1,
      selected_character_change_indexes: [0],
      selected_foreshadow_change_indexes: [0],
      opening_pov_confirmation: {
        confirmed: true,
        draft_version: 1,
        locked_character_id: 1,
        locked_character_name: '林砚',
      },
    });
  });

  it('invalidates an existing locked-POV confirmation when only the target name changes and submits the new name after reconfirmation', async () => {
    const user = userEvent.setup();
    renderResumedOpeningPovStudio();

    const originalConfirmation = await screen.findByRole('checkbox', {
      name: '我确认本章锁定 POV：林砚（限知第三人称），并以当前草稿版本 v1 写入正史',
    });
    await user.click(originalConfirmation);
    expect(originalConfirmation).toBeChecked();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled();

    approvalOpeningPovTarget.current = {
      required: true,
      locked_character_id: 1,
      locked_character_name: '林砚·新名',
    };
    vi.mocked(reviseDraft).mockResolvedValueOnce(openingPovDraft());
    await user.type(screen.getByLabelText('修订指令'), '重新加载锁定 POV 确认');
    await user.click(screen.getByRole('button', { name: '生成修订版' }));

    const renamedConfirmation = await screen.findByRole('checkbox', {
      name: '我确认本章锁定 POV：林砚·新名（限知第三人称），并以当前草稿版本 v1 写入正史',
    });
    expect(renamedConfirmation).not.toBeChecked();
    const approveButton = screen.getByRole('button', { name: '写入正史并更新世界' });
    expect(approveButton).toBeDisabled();

    await user.click(renamedConfirmation);
    await waitFor(() => expect(approveButton).toBeEnabled());
    await user.click(approveButton);

    expect(approveChapter).toHaveBeenCalledWith(11, {
      draft_version: 1,
      selected_character_change_indexes: [0],
      selected_foreshadow_change_indexes: [0],
      opening_pov_confirmation: {
        confirmed: true,
        draft_version: 1,
        locked_character_id: 1,
        locked_character_name: '林砚·新名',
      },
    });
  });

  it('clears locked-POV confirmation after a v1 opening draft is revised into v2', async () => {
    const user = userEvent.setup();
    renderResumedOpeningPovStudio();

    const v1Confirmation = await screen.findByRole('checkbox', {
      name: '我确认本章锁定 POV：林砚（限知第三人称），并以当前草稿版本 v1 写入正史',
    });
    await user.click(v1Confirmation);
    expect(v1Confirmation).toBeChecked();

    approvalPanelVersion.current = 2;
    vi.mocked(reviseDraft).mockResolvedValueOnce(openingPovDraft(2));
    await user.type(screen.getByLabelText('修订指令'), '补足林砚限知视角');
    await user.click(screen.getByRole('button', { name: '生成修订版' }));

    expect(await screen.findByText('当前草稿：v2')).toBeInTheDocument();
    const v2Confirmation = screen.getByRole('checkbox', {
      name: '我确认本章锁定 POV：林砚（限知第三人称），并以当前草稿版本 v2 写入正史',
    });
    expect(v2Confirmation).not.toBeChecked();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
  });

  it('marks stale opening quality checks as inapplicable to the current draft and locally blocks approval', async () => {
    const resumedDraft = {
      ...draftResponse,
      draft_id: 102,
      draft_version: 2,
      title: '第一章 雨巷密谈（修订版）',
      content: '修订版第一段：林砚没有立刻信任沈微霜，而是先以湿信试探她。\n\n第二段：沈微霜递来一封湿透的信。',
      change_type: 'revision',
      change_summary: '补足林砚试探沈微霜的过程',
      parent_draft_version: 1,
      quality_report: {
        profile: 'opening_chapter',
        status: 'stale',
        validation_version: 5,
        evaluated_draft_version: 1,
        current_draft_version: 2,
        checks: [
          { label: '背景建立', status: 'pass' },
          { label: '主角身份与动机', status: 'pass' },
          { label: '性格选择', status: 'pass' },
          { label: '冲突目标', status: 'pass' },
          { label: '稳定 POV', status: 'pass' },
          { label: '悬念钩子', status: 'pass' },
        ],
      },
    } as DraftResponse;
    vi.mocked(getApprovalPreview).mockResolvedValueOnce({
      chapter_id: 11,
      draft_version: 2,
      opening_pov_confirmation_target: {
        required: false,
        locked_character_id: null,
        locked_character_name: null,
      },
      source_world_version: 1,
      current_world_version: 1,
      will_increment_world_version: true,
      world_version_before: 1,
      world_version_after: 2,
      version_conflict: false,
      warnings: [],
      consistency_summary: { status: 'needs_review', total: 1, info_count: 0, warning_count: 1, blocking_count: 0 },
      consistency_warnings: [],
      character_changes: [],
      foreshadow_changes: [],
    });
    vi.mocked(getApprovalReadiness).mockResolvedValueOnce({
      chapter_id: 11,
      draft_version: 2,
      status: 'ready',
      summary: '审批检查已就绪。',
      world_version: { source_world_version: 1, current_world_version: 1, matches: true },
      checks: [],
      high_risk_items: [],
    });

    renderResumedStudio(resumedDraft, [1, 2]);

    const approvalRegion = screen.getByRole('region', { name: '质量与 Canon 审批' });
    expect(await within(approvalRegion).findByText('当前草稿未验证')).toBeInTheDocument();
    expect(within(approvalRegion).getByText('基于 v1，不适用于当前 v2')).toBeInTheDocument();
    expect(within(approvalRegion).queryByText('通过')).not.toBeInTheDocument();
    expect(within(approvalRegion).getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
  });

  it('treats a current-draft opening quality report without validation version as requiring reevaluation and prevents approval', async () => {
    const user = userEvent.setup();
    const resumedDraft = {
      ...draftResponse,
      quality_report: {
        profile: 'opening_chapter',
        status: 'pass',
        evaluated_draft_version: 1,
        checks: [
          { label: '背景建立', status: 'pass' },
          { label: '主角身份与动机', status: 'pass' },
        ],
      },
    } as DraftResponse;

    renderResumedStudio(resumedDraft);

    const approvalRegion = screen.getByRole('region', { name: '质量与 Canon 审批' });
    expect(await within(approvalRegion).findByText(/验证规则已更新|需重新评估/)).toBeInTheDocument();
    expect(within(approvalRegion).queryByText('状态：通过 · opening_chapter')).not.toBeInTheDocument();
    const approveButton = within(approvalRegion).getByRole('button', { name: '写入正史并更新世界' });
    expect(approveButton).toBeDisabled();

    await user.click(approveButton);

    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('shows a pass opening-quality report for another draft version as expired and blocks approval', async () => {
    const resumedDraft = {
      ...draftResponse,
      draft_id: 102,
      draft_version: 2,
      parent_draft_version: 1,
      quality_report: {
        profile: 'opening_chapter',
        status: 'pass',
        validation_version: 4,
        evaluated_draft_version: 1,
        current_draft_version: 1,
        checks: [
          { label: '背景建立', status: 'pass' },
          { label: '主角身份与动机', status: 'pass' },
        ],
      },
    } as DraftResponse;
    vi.mocked(getApprovalPreview).mockResolvedValueOnce({ ...await getApprovalPreview(11), draft_version: 2 });
    vi.mocked(getApprovalReadiness).mockResolvedValueOnce({ ...await getApprovalReadiness(11), draft_version: 2 });

    renderResumedStudio(resumedDraft, [1, 2]);

    const approvalRegion = screen.getByRole('region', { name: '质量与 Canon 审批' });
    expect(await within(approvalRegion).findByText('状态：已过期 · opening_chapter')).toBeInTheDocument();
    expect(within(approvalRegion).getAllByText('已过期')).toHaveLength(2);
    expect(within(approvalRegion).getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
  });

  it.each([
    ['preview', 'approval preview'],
    ['readiness', 'approval readiness'],
  ] as const)('fails closed when %s belongs to a different draft version', async (mismatchedPanel, _panelLabel) => {
    if (mismatchedPanel === 'preview') {
      vi.mocked(getApprovalPreview).mockResolvedValueOnce({ ...await getApprovalPreview(11), draft_version: 2 });
    } else {
      vi.mocked(getApprovalReadiness).mockResolvedValueOnce({ ...await getApprovalReadiness(11), draft_version: 2 });
    }

    renderResumedStudio();

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('审批检查版本不一致');
    expect(screen.queryByText('Approval Readiness')).not.toBeInTheDocument();
    expect(screen.queryByText('写入正史前确认')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('requires explicit confirmation before abandoning and keeps the chapter when cancelled', async () => {
    const user = userEvent.setup();
    renderResumedStudio();

    await user.click(screen.getByRole('button', { name: '放弃当前章节' }));

    const dialog = screen.getByRole('dialog', { name: '放弃当前章节？' });
    expect(dialog).toHaveTextContent('章节、草稿版本和已生成报告都会保留');
    expect(dialog).toHaveTextContent('不会写入正史');
    expect(dialog).toHaveTextContent('不可恢复');
    expect(abandonChapter).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: '继续创作' }));

    expect(screen.queryByRole('dialog', { name: '放弃当前章节？' })).not.toBeInTheDocument();
    expect(abandonChapter).not.toHaveBeenCalled();
  });

  it('exits only after the server confirms the abandoned terminal state', async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    const onAbandoned = vi.fn();
    renderResumedStudio(draftResponse, [1], { onBack, onAbandoned });

    await user.click(screen.getByRole('button', { name: '放弃当前章节' }));
    await user.click(screen.getByRole('button', { name: '确认放弃并结束创作' }));

    await waitFor(() => expect(onAbandoned).toHaveBeenCalledWith(7));
    expect(abandonChapter).toHaveBeenCalledWith(11);
    expect(onBack).not.toHaveBeenCalled();
  });

  it('stays in Studio when the server does not confirm the abandoned state', async () => {
    const user = userEvent.setup();
    const onAbandoned = vi.fn();
    vi.mocked(abandonChapter).mockResolvedValueOnce({
      id: 11,
      world_id: 7,
      title: '第一章 雨巷密谈',
      status: 'reviewing',
      draft_version: 1,
      approved_version: null,
      base_world_version: 1,
      approved_content: null,
      chapter_goal: '推进雨巷密谈',
      outline_beats: [],
      outline_context: {},
      critique_report: {},
      execution_context: executionContext,
    });
    renderResumedStudio(draftResponse, [1], { onAbandoned });

    await user.click(screen.getByRole('button', { name: '放弃当前章节' }));
    await user.click(screen.getByRole('button', { name: '确认放弃并结束创作' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('服务器未返回 abandoned 状态');
    expect(screen.getByRole('dialog', { name: '放弃当前章节？' })).toBeInTheDocument();
    expect(onAbandoned).not.toHaveBeenCalled();
  });

  it('closes the confirmation with Escape and restores focus to the danger trigger', async () => {
    const user = userEvent.setup();
    renderResumedStudio();
    const trigger = screen.getByRole('button', { name: '放弃当前章节' });

    await user.click(trigger);
    expect(await screen.findByRole('dialog', { name: '放弃当前章节？' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '继续创作' })).toHaveFocus();

    await user.keyboard('{Escape}');

    expect(screen.queryByRole('dialog', { name: '放弃当前章节？' })).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });

  it('stays in Studio and shows the server error when abandoning fails', async () => {
    const user = userEvent.setup();
    const onAbandoned = vi.fn();
    vi.mocked(abandonChapter).mockRejectedValueOnce(new Error('放弃请求暂不可用'));
    renderResumedStudio(draftResponse, [1], { onAbandoned });

    await user.click(screen.getByRole('button', { name: '放弃当前章节' }));
    await user.click(screen.getByRole('button', { name: '确认放弃并结束创作' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('放弃请求暂不可用');
    expect(screen.getByRole('dialog', { name: '放弃当前章节？' })).toBeInTheDocument();
    expect(onAbandoned).not.toHaveBeenCalled();
  });

  it('locks the confirmation controls while the abandon request is pending', async () => {
    const user = userEvent.setup();
    const onAbandoned = vi.fn();
    let resolveAbandon!: (value: Awaited<ReturnType<typeof abandonChapter>>) => void;
    vi.mocked(abandonChapter).mockReturnValueOnce(new Promise((resolve) => { resolveAbandon = resolve; }));
    renderResumedStudio(draftResponse, [1], { onAbandoned });

    await user.click(screen.getByRole('button', { name: '放弃当前章节' }));
    await user.click(screen.getByRole('button', { name: '确认放弃并结束创作' }));

    expect(screen.getByRole('button', { name: '继续创作' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '正在放弃…' })).toBeDisabled();
    expect(abandonChapter).toHaveBeenCalledTimes(1);

    resolveAbandon({
      id: 11,
      world_id: 7,
      title: '第一章 雨巷密谈',
      status: 'abandoned',
      draft_version: 1,
      approved_version: null,
      base_world_version: 1,
      approved_content: null,
      chapter_goal: '推进雨巷密谈',
      outline_beats: [],
      outline_context: {},
      critique_report: {},
      execution_context: executionContext,
    });
    await waitFor(() => expect(onAbandoned).toHaveBeenCalledWith(7));
  });

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

  it('resumes an outlined first-chapter session without creating a duplicate chapter', async () => {
    render(
      <StudioPage
        world={world}
        launchContext={{
          initialChapterGoal: '让林砚在雨巷第一次试探沈微霜。',
          autoDraftFirstChapter: true,
          resumeSession: {
            chapter: {
              id: 11,
              world_id: 7,
              title: '让林砚在雨巷第一次试探沈微霜。',
              status: 'outlined',
              draft_version: 1,
              approved_version: null,
              base_world_version: 1,
              approved_content: null,
              chapter_goal: '让林砚在雨巷第一次试探沈微霜。',
              outline_beats: [{ beat_id: 'beat-1', summary: '雨巷交换线索', pov_character: '林砚', location: '雨巷', emotional_arc: '警觉 -> 犹疑', key_dialogue_hints: [] }],
              outline_context: { core_conflict: '判断沈微霜是否可信' },
              critique_report: {},
              execution_context: executionContext,
            },
            draft: null,
            draft_versions: [],
          },
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    expect(await screen.findByText('Writer Draft')).toBeInTheDocument();
    expect(createChapter).not.toHaveBeenCalled();
    expect(generateOutline).not.toHaveBeenCalled();
    expect(writeChapter).toHaveBeenCalledTimes(1);
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('restores complete draft version history without regenerating or approving it', async () => {
    const user = userEvent.setup();
    const resumedDraft = {
      ...draftResponse,
      draft_id: 103,
      draft_version: 3,
      content: '第三版正文：林砚在雨巷口重新核对湿信。',
      change_type: 'stash',
      change_summary: '第三版快照',
      parent_draft_version: 2,
    };
    render(
      <StudioPage
        world={world}
        launchContext={{
          initialChapterGoal: '让林砚在雨巷第一次试探沈微霜。',
          resumeSession: {
            chapter: {
              id: 11,
              world_id: 7,
              title: draftResponse.title,
              status: 'reviewing',
              draft_version: 3,
              approved_version: null,
              base_world_version: 1,
              approved_content: null,
              chapter_goal: '让林砚在雨巷第一次试探沈微霜。',
              outline_beats: draftResponse.outline_beats ?? [],
              outline_context: draftResponse.outline_context ?? {},
              critique_report: {},
              execution_context: executionContext,
            },
            draft: resumedDraft,
            draft_versions: [1, 2, 3],
          },
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    expect(await screen.findByText('Writer Draft')).toBeInTheDocument();
    await waitFor(() => expect(getApprovalPreview).toHaveBeenCalledWith(11));
    expect(getApprovalReadiness).toHaveBeenCalledWith(11);
    const versionSelect = screen.getByLabelText('草稿版本');
    expect(versionSelect).toHaveValue('3');
    expect(screen.getAllByRole('option').map((option) => option.textContent)).toEqual(['v1', 'v2', 'v3']);

    await user.click(screen.getByRole('button', { name: '编辑正文' }));
    expect(versionSelect).toBeDisabled();
    expect(screen.getByRole('button', { name: '保存修改' })).toBeEnabled();
    await user.selectOptions(versionSelect, '1');
    expect(versionSelect).toHaveValue('3');
    expect(getDraftVersion).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: '取消' }));
    await user.selectOptions(versionSelect, '1');

    await waitFor(() => expect(getDraftVersion).toHaveBeenCalledWith(11, 1));
    expect(versionSelect).toHaveValue('1');
    expect(screen.getAllByText('第一段：林砚停在雨巷口。').length).toBeGreaterThan(0);
    expect(screen.queryByLabelText('编辑草稿内容')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '保存修改' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '编辑正文' })).toBeDisabled();
    expect(createChapter).not.toHaveBeenCalled();
    expect(generateOutline).not.toHaveBeenCalled();
    expect(writeChapter).not.toHaveBeenCalled();
    expect(editDraft).not.toHaveBeenCalled();
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('keeps approval disabled while resumed draft review panels are loading', async () => {
    let resolvePreview!: (value: Awaited<ReturnType<typeof getApprovalPreview>>) => void;
    vi.mocked(getApprovalPreview).mockImplementationOnce(async () => new Promise<Awaited<ReturnType<typeof getApprovalPreview>>>((resolve) => {
      resolvePreview = resolve;
    }));
    render(
      <StudioPage
        world={world}
        launchContext={{
          resumeSession: {
            chapter: {
              id: 11,
              world_id: 7,
              title: draftResponse.title,
              status: 'reviewing',
              draft_version: 1,
              approved_version: null,
              base_world_version: 1,
              approved_content: null,
              chapter_goal: '推进雨巷密谈',
              outline_beats: [],
              outline_context: {},
              critique_report: {},
              execution_context: executionContext,
            },
            draft: draftResponse,
            draft_versions: [1],
          },
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    expect(await screen.findByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
    expect(approveChapter).not.toHaveBeenCalled();

    resolvePreview(await getApprovalPreview(11));

    await waitFor(() => expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled());
  });

  it('shows a retry path and keeps approval fail-closed when approval preview loading fails', async () => {
    const user = userEvent.setup();
    vi.mocked(getApprovalPreview).mockRejectedValueOnce(new Error('预览服务暂不可用'));
    renderResumedStudio();

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('审批检查加载失败：预览服务暂不可用');
    expect(alert).toHaveTextContent('重试不会写入正史');
    const approveButton = screen.getByRole('button', { name: '写入正史并更新世界' });
    expect(approveButton).toBeDisabled();

    await user.click(approveButton);
    expect(approveChapter).not.toHaveBeenCalled();
    expect(screen.getAllByText(draftResponse.title)).not.toHaveLength(0);
    expect(screen.getByText(draftResponse.context_summary)).toBeInTheDocument();
    expect(screen.getByLabelText('草稿版本')).toHaveValue('1');
    expect(createChapter).not.toHaveBeenCalled();
    expect(generateOutline).not.toHaveBeenCalled();
    expect(writeChapter).not.toHaveBeenCalled();
    expect(editDraft).not.toHaveBeenCalled();
    expect(reviseDraft).not.toHaveBeenCalled();
    expect(reviseParagraph).not.toHaveBeenCalled();
  });

  it('keeps approval fail-closed when readiness loading fails even if preview succeeds', async () => {
    vi.mocked(getApprovalReadiness).mockRejectedValueOnce(new Error('准备度服务暂不可用'));
    renderResumedStudio();

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('审批检查加载失败：准备度服务暂不可用');
    expect(getApprovalPreview).toHaveBeenCalledWith(11);
    expect(screen.getByRole('button', { name: '重试审批检查' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('retries approval checks without losing the draft version or approval selections', async () => {
    const user = userEvent.setup();
    vi.mocked(getApprovalReadiness).mockRejectedValueOnce(new Error('准备度服务暂不可用'));
    renderResumedStudio();

    await screen.findByRole('button', { name: '重试审批检查' });
    await user.click(screen.getByRole('button', { name: '重试审批检查' }));

    expect(await screen.findByText('写入正史前确认')).toBeInTheDocument();
    expect(screen.queryByText(/审批检查加载失败/)).not.toBeInTheDocument();
    expect(screen.getAllByText(draftResponse.title)).not.toHaveLength(0);
    expect(screen.getByText(draftResponse.context_summary)).toBeInTheDocument();
    expect(screen.getByLabelText('草稿版本')).toHaveValue('1');
    expect(screen.getByRole('checkbox', { name: /角色：林砚/ })).toBeChecked();
    expect(screen.getByRole('checkbox', { name: /伏笔：裂纹玉佩/ })).toBeChecked();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled();
    expect(getApprovalPreview).toHaveBeenCalledTimes(2);
    expect(getApprovalReadiness).toHaveBeenCalledTimes(2);
    expect(approveChapter).not.toHaveBeenCalled();
    expect(createChapter).not.toHaveBeenCalled();
    expect(generateOutline).not.toHaveBeenCalled();
    expect(writeChapter).not.toHaveBeenCalled();
    expect(editDraft).not.toHaveBeenCalled();
    expect(reviseDraft).not.toHaveBeenCalled();
    expect(reviseParagraph).not.toHaveBeenCalled();
  });

  it('preserves user approval selections across a failed refresh and retry', async () => {
    const user = userEvent.setup();
    renderResumedStudio();

    const characterChange = await screen.findByRole('checkbox', { name: /角色：林砚/ });
    await user.click(characterChange);
    await waitFor(() => expect(characterChange).not.toBeChecked());

    vi.mocked(getApprovalReadiness).mockRejectedValueOnce(new Error('准备度服务暂不可用'));
    await user.click(screen.getByRole('button', { name: '生成 Critic 报告' }));
    await user.click(await screen.findByRole('button', { name: '重试审批检查' }));

    expect(await screen.findByText('写入正史前确认')).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /角色：林砚/ })).not.toBeChecked();
    expect(screen.getByRole('checkbox', { name: /伏笔：裂纹玉佩/ })).toBeChecked();
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('ignores a retried review-panel response that arrives after switching to history', async () => {
    const user = userEvent.setup();
    vi.mocked(getApprovalPreview).mockRejectedValueOnce(new Error('预览服务暂不可用'));
    let resolveRetryPreview!: (value: Awaited<ReturnType<typeof getApprovalPreview>>) => void;
    vi.mocked(getApprovalPreview).mockImplementationOnce(async () => new Promise<Awaited<ReturnType<typeof getApprovalPreview>>>((resolve) => {
      resolveRetryPreview = resolve;
    }));
    const resumedDraft = {
      ...draftResponse,
      draft_id: 102,
      draft_version: 2,
      parent_draft_version: 1,
      content: '第二版正文：林砚在雨巷口试探沈微霜。',
    };
    renderResumedStudio(resumedDraft, [1, 2]);

    await user.click(await screen.findByRole('button', { name: '重试审批检查' }));
    await user.selectOptions(screen.getByLabelText('草稿版本'), '1');
    expect((await screen.findAllByText('第一段：林砚停在雨巷口。')).length).toBeGreaterThan(0);

    resolveRetryPreview({ ...await getApprovalPreview(11), draft_version: 2 });

    await waitFor(() => expect(screen.queryByText('写入正史前确认')).not.toBeInTheDocument());
    expect(screen.queryByText('Approval Readiness')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '重试审批检查' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('ignores a resumed review-panel response that arrives after switching to history', async () => {
    const user = userEvent.setup();
    let resolvePreview!: (value: Awaited<ReturnType<typeof getApprovalPreview>>) => void;
    vi.mocked(getApprovalPreview).mockImplementationOnce(async () => new Promise<Awaited<ReturnType<typeof getApprovalPreview>>>((resolve) => {
      resolvePreview = resolve;
    }));
    const resumedDraft = {
      ...draftResponse,
      draft_id: 102,
      draft_version: 2,
      parent_draft_version: 1,
      content: '第二版正文：林砚在雨巷口试探沈微霜。',
    };
    render(
      <StudioPage
        world={world}
        launchContext={{
          resumeSession: {
            chapter: {
              id: 11,
              world_id: 7,
              title: resumedDraft.title,
              status: 'reviewing',
              draft_version: 2,
              approved_version: null,
              base_world_version: 1,
              approved_content: null,
              chapter_goal: '推进雨巷密谈',
              outline_beats: [],
              outline_context: {},
              critique_report: {},
              execution_context: executionContext,
            },
            draft: resumedDraft,
            draft_versions: [1, 2],
          },
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    await user.selectOptions(await screen.findByLabelText('草稿版本'), '1');
    expect((await screen.findAllByText('第一段：林砚停在雨巷口。')).length).toBeGreaterThan(0);

    resolvePreview(await getApprovalPreview(11));

    await waitFor(() => expect(screen.queryByText('写入正史前确认')).not.toBeInTheDocument());
    expect(screen.queryByText('Approval Readiness')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
  });

  it('retries a failed automatic first-chapter chapter creation before continuing to Studio review', async () => {
    const user = userEvent.setup();
    vi.mocked(createChapter).mockRejectedValueOnce(new Error('CREATE_CHAPTER_FAILED'));

    render(
      <StudioPage
        world={world}
        launchContext={{
          initialChapterGoal: '让林砚在雨巷第一次试探沈微霜。',
          executionContext,
          autoDraftFirstChapter: true,
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('已创建的世界和当前创作进度都已保留，可以直接重试。');
    expect(alert).not.toHaveTextContent('CREATE_CHAPTER_FAILED');
    expect(screen.getByText('世界进度：1')).toBeInTheDocument();
    expect(screen.queryByText('Chapter Session')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '重试生成第一章草稿' }));

    expect(await screen.findByText('Writer Draft')).toBeInTheDocument();
    expect(createChapter).toHaveBeenCalledTimes(2);
    expect(generateOutline).toHaveBeenCalledTimes(1);
    expect(writeChapter).toHaveBeenCalledTimes(1);
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('stops automatic first-chapter generation when another active chapter already exists', async () => {
    vi.mocked(createChapter).mockRejectedValueOnce(new Error('ACTIVE_CHAPTER_EXISTS'));

    render(
      <StudioPage
        world={world}
        launchContext={{
          initialChapterGoal: '让林砚在雨巷第一次试探沈微霜。',
          executionContext,
          autoDraftFirstChapter: true,
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    expect(await screen.findByRole('alert')).toHaveTextContent('这个世界已有进行中的章节。请返回世界页恢复该章节');
    expect(screen.queryByRole('button', { name: '重试生成第一章草稿' })).not.toBeInTheDocument();
    expect(createChapter).toHaveBeenCalledTimes(1);
    expect(generateOutline).not.toHaveBeenCalled();
    expect(writeChapter).not.toHaveBeenCalled();
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('retries a failed automatic first-chapter outline without creating a duplicate chapter', async () => {
    const user = userEvent.setup();
    vi.mocked(generateOutline).mockRejectedValueOnce(new Error('GENERATE_OUTLINE_FAILED'));

    render(
      <StudioPage
        world={world}
        launchContext={{
          initialChapterGoal: '让林砚在雨巷第一次试探沈微霜。',
          executionContext,
          autoDraftFirstChapter: true,
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('已创建的世界和当前创作进度都已保留，可以直接重试。');
    expect(alert).not.toHaveTextContent('GENERATE_OUTLINE_FAILED');
    expect(screen.getByText('世界进度：1')).toBeInTheDocument();
    expect(screen.getByText('Chapter Session')).toBeInTheDocument();
    expect(screen.queryByText('Outliner Beats')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '重试生成第一章草稿' }));

    expect(await screen.findByText('Writer Draft')).toBeInTheDocument();
    expect(createChapter).toHaveBeenCalledTimes(1);
    expect(generateOutline).toHaveBeenCalledTimes(2);
    expect(writeChapter).toHaveBeenCalledTimes(1);
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('retries a failed automatic first-chapter draft without creating a duplicate chapter', async () => {
    const user = userEvent.setup();
    vi.mocked(writeChapter).mockRejectedValueOnce(new Error('MODEL_REQUEST_FAILED'));

    render(
      <StudioPage
        world={world}
        launchContext={{
          initialChapterGoal: '让林砚在雨巷第一次试探沈微霜。',
          executionContext,
          autoDraftFirstChapter: true,
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('第一章草稿暂未生成。已创建的世界和当前创作进度都已保留，可以直接重试。');
    expect(alert).not.toHaveTextContent('MODEL_REQUEST_FAILED');
    expect(screen.getByLabelText('章节目标')).toHaveValue('让林砚在雨巷第一次试探沈微霜。');
    expect(screen.getByText('世界进度：1')).toBeInTheDocument();
    expect(screen.queryByText('Writer Draft')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '重试生成第一章草稿' }));

    expect(await screen.findByText('Writer Draft')).toBeInTheDocument();
    expect(screen.getAllByText('第一章 雨巷密谈')).toHaveLength(2);
    expect(createChapter).toHaveBeenCalledTimes(1);
    expect(generateOutline).toHaveBeenCalledTimes(1);
    expect(writeChapter).toHaveBeenCalledTimes(2);
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('shows launch execution context summary and submits edited context when creating chapter', async () => {
    const user = userEvent.setup();
    render(<StudioPage world={world} launchContext={{ initialChapterGoal: executionContext.goal, executionContext }} onBack={vi.fn()} onApproved={vi.fn()} />);

    expect(screen.getByText('本章设定（本章要写什么）')).toBeInTheDocument();
    expect(screen.getByText('来源：下一章准备台')).toBeInTheDocument();
    expect(screen.getByText('推荐 POV：林砚')).toBeInTheDocument();
    expect(screen.getByText('优先角色：林砚')).toBeInTheDocument();
    expect(screen.getByText('优先伏笔：裂纹玉佩')).toBeInTheDocument();
    expect(screen.getByText('下一章需要补足试探过程。')).toBeInTheDocument();

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
    expect(await screen.findByText('已冻结本章设定：next_chapter_prep · v2')).toBeInTheDocument();
  });

  it('shows serial-plan review guardrails from execution context before creating a chapter', async () => {
    render(
      <StudioPage
        world={world}
        launchContext={{
          initialChapterGoal: executionContext.goal,
          executionContext: {
            ...executionContext,
            continuity_warnings: [
              { severity: 'info', category: 'serial_plan_review_boundary', message: '连载队列只是只读计划，不会批量创建章节或正文。', related_character_ids: [], related_foreshadow_ids: [] },
              { severity: 'info', category: 'serial_plan_review_boundary', message: '写入正史前必须由用户审稿确认。', related_character_ids: [], related_foreshadow_ids: [] },
            ],
          },
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    expect(screen.getByText('连续性提醒：2 条')).toBeInTheDocument();
    expect(screen.getByText('连载队列只是只读计划，不会批量创建章节或正文。')).toBeInTheDocument();
    expect(screen.getByText('写入正史前必须由用户审稿确认。')).toBeInTheDocument();
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('shows the writing style handbook reference in execution context without writing canon', async () => {
    render(
      <StudioPage
        world={world}
        launchContext={{
          initialChapterGoal: executionContext.goal,
          executionContext: {
            ...executionContext,
            style_handbook_reference: {
              source_title: '参考片段',
              source_rights: 'general_reference',
              handbook: {
                narrative_pacing: { label: '叙事节奏', value: '中速推进。', evidence: null },
                language_density: { label: '语言密度', value: '中等语言密度。', evidence: null },
                dialogue_ratio: { label: '对白比例', value: '对白与叙述交替。', evidence: null },
                scene_progression: { label: '场景推进', value: '用意象带动转场。', evidence: null },
                suspense_structure: { label: '悬念结构', value: '每节保留待解问题。', evidence: null },
                relationship_tension: { label: '人物关系张力', value: '围绕亏欠推进。', evidence: null },
                foreshadowing_pattern: { label: '伏笔埋设/回收方式', value: '先给异常，再延迟解释。', evidence: null },
                do_guidelines: ['保留抽象节奏。'],
                avoid_guidelines: ['不要复用原文句子、人物名、专有设定或标志性桥段。'],
                originality_guidelines: ['正式章节仍需 Studio 审稿。'],
              },
              safety_notes: ['风格手册只是写作参考，不写入 canon。'],
            },
          },
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    expect(screen.getByText('写作风格参考：参考片段（仅抽象风格维度，不写入正史）')).toBeInTheDocument();
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('auto-generates a first chapter draft from launch context without approving canon', async () => {
    render(
      <StudioPage
        world={world}
        launchContext={{
          initialChapterGoal: '让伊莱发现自己的死因记录被烧穿。',
          executionContext: {
            source: 'manual',
            source_world_version: 1,
            next_chapter_number: 1,
            goal: '让伊莱发现自己的死因记录被烧穿。',
            recommended_pov: { character_id: null, name: null },
            source_signals: ['world_creation_draft'],
            priority_characters: [],
            priority_foreshadows: [],
            progression_hints: [],
            continuity_warnings: [],
            recent_events: [],
            material_references: [],
          },
          autoDraftFirstChapter: true,
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    await waitFor(() => expect(createChapter).toHaveBeenCalledWith(7, expect.objectContaining({
      chapter_goal: '让伊莱发现自己的死因记录被烧穿。',
      execution_context: expect.objectContaining({
        source: 'manual',
        source_signals: ['world_creation_draft'],
      }),
    })));
    expect(generateOutline).toHaveBeenCalledWith(11, { chapter_context: '让伊莱发现自己的死因记录被烧穿。' });
    expect(writeChapter).toHaveBeenCalledWith(11, expect.objectContaining({ outline_beats: expect.any(Array) }));
    expect(getApprovalPreview).toHaveBeenCalledWith(11);
    expect(approveChapter).not.toHaveBeenCalled();
    expect(await screen.findByText('草稿已进入 Studio，确认后再写入正史。')).toBeInTheDocument();
    expect(await screen.findByText('写入正史前确认')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled();
  });

  it('creates manual context when Studio opens without NCC execution context', async () => {
    const user = userEvent.setup();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    expect(screen.getByText('本章暂无来自下一章准备台的设定。创建章节时会根据当前目标生成手动设定快照。')).toBeInTheDocument();
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

    expect(await screen.findByText('本章设定快照')).toBeInTheDocument();
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
    expect(screen.getByText('写入正史前确认')).toBeInTheDocument();
    expect(screen.getByText('世界进度：1 → 2')).toBeInTheDocument();
    expect(screen.getByText('Approval Readiness')).toBeInTheDocument();
    expect(screen.getByText('建议复核后批准')).toBeInTheDocument();
    expect(screen.getByText('Critic 高风险')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled();

    await user.click(screen.getByRole('button', { name: '生成 Critic 报告' }));
    expect(await screen.findByText('总评分：78/100')).toBeInTheDocument();
    expect(screen.getByText('Critic 发现高风险问题，建议修订后再批准。')).toBeInTheDocument();
    expect(screen.getByText('林砚突然信任沈微霜，与当前谨慎状态冲突。')).toBeInTheDocument();
  });

  it('uses story-world terminology for the main canon workflow', async () => {
    const user = userEvent.setup();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    expect(screen.getByText('创作流程')).toBeInTheDocument();
    expect(screen.getByText('世界进度：1')).toBeInTheDocument();

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

    expect(await screen.findByText('写入正史前确认')).toBeInTheDocument();
    expect(screen.getByText('设定冲突检查')).toBeInTheDocument();
    expect(screen.getByText('世界进度：1 → 2')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled();
  });

  it('shows story-operation waiting copy while generating the outline', async () => {
    const user = userEvent.setup();
    let resolveOutline!: (value: Awaited<ReturnType<typeof generateOutline>>) => void;
    vi.mocked(generateOutline).mockImplementationOnce(async () => new Promise<Awaited<ReturnType<typeof generateOutline>>>((resolve) => {
      resolveOutline = resolve;
    }));
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));

    expect(await screen.findByRole('button', { name: '编剧室正在排布章节骨架…' })).toBeInTheDocument();

    resolveOutline({
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
    });
    await screen.findByText('可编辑节拍卡');
  });

  it('shows story-operation waiting copy while generating the critic report', async () => {
    const user = userEvent.setup();
    let resolveCritic!: (value: Awaited<ReturnType<typeof generateCriticReport>>) => void;
    vi.mocked(generateCriticReport).mockImplementationOnce(async () => new Promise<Awaited<ReturnType<typeof generateCriticReport>>>((resolve) => {
      resolveCritic = resolve;
    }));
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(screen.getByRole('button', { name: '生成 Critic 报告' }));

    expect(await screen.findByRole('button', { name: '评论席正在检查节奏与设定…' })).toBeInTheDocument();

    resolveCritic({
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
      issues: [],
      suggestions: [],
      created_at: '2026-05-29T00:00:00Z',
    });
    await screen.findByText('总评分：78/100');
  });

  it('shows story-operation waiting copy while generating the draft', async () => {
    const user = userEvent.setup();
    let resolveWrite!: (value: DraftResponse) => void;
    vi.mocked(writeChapter).mockImplementationOnce(async () => new Promise<DraftResponse>((resolve) => {
      resolveWrite = resolve;
    }));
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(screen.getByRole('button', { name: '基于大纲生成正文' }));

    expect(await screen.findByRole('button', { name: '导演正在拆场景…' })).toBeInTheDocument();

    resolveWrite(draftResponse);
    await screen.findByText('写入正史前确认');
  });

  it('shows canon-writing waiting copy while approving the draft', async () => {
    const user = userEvent.setup();
    let resolveApprove!: (value: Awaited<ReturnType<typeof approveChapter>>) => void;
    vi.mocked(approveChapter).mockImplementationOnce(async () => new Promise<Awaited<ReturnType<typeof approveChapter>>>((resolve) => {
      resolveApprove = resolve;
    }));
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));

    expect(await screen.findByRole('button', { name: '正在写入正史…' })).toBeInTheDocument();

    resolveApprove({ status: 'approved' } as Awaited<ReturnType<typeof approveChapter>>);
    await waitFor(() => expect(approveChapter).toHaveBeenCalled());
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
    expect(getApprovalReadiness).toHaveBeenCalledTimes(2);
    expect(await screen.findByText('角色弧线报告')).toBeInTheDocument();
    expect(screen.getByText('本章推动林砚从被动等待转向主动追查湿信来源。')).toBeInTheDocument();
    expect(screen.getByText('林砚 · protagonist')).toBeInTheDocument();
    expect(screen.getByText('让林砚做出是否相信沈微霜的选择')).toBeInTheDocument();
  });

  it('blocks approval controls and command entry when approval readiness is blocked', async () => {
    const user = userEvent.setup();
    vi.mocked(getApprovalReadiness).mockResolvedValueOnce({
      chapter_id: 11,
      draft_version: 1,
      status: 'blocked',
      summary: '存在阻塞项，暂不可批准。',
      world_version: { source_world_version: 1, current_world_version: 2, matches: false },
      checks: [
        { key: 'world_version', label: '世界版本一致', status: 'fail', message: '世界版本已变化，请重新生成草稿后再批准。', details: {} },
      ],
      high_risk_items: [],
    });
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

    expect(await screen.findByText('暂不可批准')).toBeInTheDocument();
    expect(screen.getByText('世界版本：v1 → v2')).toBeInTheDocument();
    expect(screen.getByText('世界版本已变化，请重新生成草稿后再批准。')).toBeInTheDocument();
    const approveButton = screen.getByRole('button', { name: '写入正史并更新世界' });
    expect(approveButton).toBeDisabled();
    await user.click(approveButton);
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('generates a full-draft revision from review context and shows parent diff', async () => {
    approvalPanelVersion.current = 2;
    const user = userEvent.setup();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

    expect(await screen.findByText('Draft Revision Loop')).toBeInTheDocument();
    await user.type(screen.getByLabelText('修订指令'), '补足林砚试探沈微霜的过程');
    await user.click(screen.getByRole('button', { name: '生成修订版' }));

    expect(reviseDraft).toHaveBeenCalledWith(11, { instruction: '补足林砚试探沈微霜的过程' });
    expect(await screen.findByText('第一章 雨巷密谈（修订版）')).toBeInTheDocument();
    expect(screen.getByText('当前草稿：v2')).toBeInTheDocument();
    expect(screen.getByText('父版本：v1')).toBeInTheDocument();
    expect(screen.getByText('最近修改：补足林砚试探沈微霜的过程')).toBeInTheDocument();
    expect(screen.getByText('v1 → v2')).toBeInTheDocument();
    expect(getApprovalReadiness).toHaveBeenCalledTimes(2);
  });

  it('switches to parent draft as a read-only historical version and disables approval', async () => {
    approvalPanelVersion.current = 2;
    const user = userEvent.setup();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.type(await screen.findByLabelText('修订指令'), '补足林砚试探沈微霜的过程');
    await user.click(screen.getByRole('button', { name: '生成修订版' }));
    await user.click(screen.getByRole('button', { name: '生成 Critic 报告' }));
    await user.click(screen.getByRole('button', { name: '生成角色弧线报告' }));

    expect(await screen.findByText('Critic 报告')).toBeInTheDocument();
    expect(screen.getByText('角色弧线报告')).toBeInTheDocument();
    expect(screen.getByText('写入正史前确认')).toBeInTheDocument();
    expect(screen.getByText('Approval Readiness')).toBeInTheDocument();

    const versionSelect = await screen.findByLabelText('草稿版本');
    await user.selectOptions(versionSelect, '1');

    expect(getDraftVersion).toHaveBeenCalledWith(11, 1);
    expect((await screen.findAllByText('第一段：林砚停在雨巷口。')).length).toBeGreaterThan(0);
    expect(screen.getByText('正在查看历史版本，切回最新版本后才能批准。')).toBeInTheDocument();
    expect(screen.queryByText('写入正史前确认')).not.toBeInTheDocument();
    expect(screen.queryByText('Approval Readiness')).not.toBeInTheDocument();
    expect(screen.queryByText('Critic 报告')).not.toBeInTheDocument();
    expect(screen.queryByText('角色弧线报告')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '生成大纲' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '基于大纲生成正文' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '生成 Critic 报告' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '生成角色弧线报告' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '暂存当前草稿' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '生成修订版' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '编辑正文' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '驳回' })).toBeDisabled();
    expect(screen.getAllByRole('button', { name: '重写本段' })[0]).toBeDisabled();
    expect(screen.getAllByRole('button', { name: '润色本段' })[0]).toBeDisabled();
    expect(screen.queryByRole('checkbox', { name: /角色：林砚/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('checkbox', { name: /伏笔：裂纹玉佩/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();

    vi.mocked(generateOutline).mockClear();
    vi.mocked(writeChapter).mockClear();
    vi.mocked(generateCriticReport).mockClear();
    vi.mocked(generateCharacterArcReport).mockClear();
    vi.mocked(checkApprovalConsistency).mockClear();
    vi.mocked(stashDraft).mockClear();
    vi.mocked(reviseDraft).mockClear();
    vi.mocked(reviseParagraph).mockClear();
    vi.mocked(getApprovalPreview).mockClear();
    vi.mocked(getApprovalReadiness).mockClear();
    await user.click(screen.getByRole('button', { name: '生成大纲' }));
    await user.click(screen.getByRole('button', { name: '基于大纲生成正文' }));
    await user.click(screen.getByRole('button', { name: '生成 Critic 报告' }));
    await user.click(screen.getByRole('button', { name: '生成角色弧线报告' }));
    await user.click(screen.getByRole('button', { name: '暂存当前草稿' }));
    await user.click(screen.getByRole('button', { name: '生成修订版' }));

    expect(generateOutline).not.toHaveBeenCalled();
    expect(writeChapter).not.toHaveBeenCalled();
    expect(generateCriticReport).not.toHaveBeenCalled();
    expect(generateCharacterArcReport).not.toHaveBeenCalled();
    expect(checkApprovalConsistency).not.toHaveBeenCalled();
    expect(stashDraft).not.toHaveBeenCalled();
    expect(reviseDraft).not.toHaveBeenCalled();
    expect(reviseParagraph).not.toHaveBeenCalled();
    expect(editDraft).not.toHaveBeenCalled();
    expect(rejectDraft).not.toHaveBeenCalled();
    expect(approveChapter).not.toHaveBeenCalled();
    expect(getApprovalPreview).not.toHaveBeenCalled();
    expect(getApprovalReadiness).not.toHaveBeenCalled();

    await user.selectOptions(versionSelect, '2');

    await waitFor(() => expect(versionSelect).toHaveValue('2'));
    await waitFor(() => expect(getApprovalPreview).toHaveBeenCalledWith(11));
    expect(getApprovalReadiness).toHaveBeenCalledWith(11);
    expect(screen.getByText('写入正史前确认')).toBeInTheDocument();
    expect(screen.getByText('Approval Readiness')).toBeInTheDocument();
    expect(screen.queryByText('Critic 报告')).not.toBeInTheDocument();
    expect(screen.queryByText('角色弧线报告')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '生成大纲' })).toBeEnabled();
    expect(screen.getByRole('button', { name: '基于大纲生成正文' })).toBeEnabled();
    expect(screen.getByRole('button', { name: '生成 Critic 报告' })).toBeEnabled();
    expect(screen.getByRole('button', { name: '生成角色弧线报告' })).toBeEnabled();
    expect(screen.getByRole('button', { name: '暂存当前草稿' })).toBeEnabled();
    expect(screen.getByRole('button', { name: '生成修订版' })).toBeEnabled();
    expect(screen.getByRole('button', { name: '编辑正文' })).toBeEnabled();
    expect(screen.getByRole('button', { name: '驳回' })).toBeEnabled();
    expect(screen.getByRole('checkbox', { name: /角色：林砚/ })).toBeEnabled();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled();

    await user.click(screen.getByRole('button', { name: '生成 Critic 报告' }));
    expect(generateCriticReport).toHaveBeenCalledWith(11);
  });

  it('ignores a stale consistency response after switching away and back to the latest draft', async () => {
    approvalPanelVersion.current = 2;
    const user = userEvent.setup();
    let resolveConsistency!: (value: Awaited<ReturnType<typeof checkApprovalConsistency>>) => void;
    vi.mocked(checkApprovalConsistency).mockImplementationOnce(async () => new Promise<Awaited<ReturnType<typeof checkApprovalConsistency>>>((resolve) => {
      resolveConsistency = resolve;
    }));
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.type(await screen.findByLabelText('修订指令'), '补足林砚试探沈微霜的过程');
    await user.click(screen.getByRole('button', { name: '生成修订版' }));

    const versionSelect = screen.getByLabelText('草稿版本');
    await user.click(screen.getByRole('checkbox', { name: /伏笔：裂纹玉佩/ }));
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();

    await user.selectOptions(versionSelect, '1');
    await user.selectOptions(versionSelect, '2');
    await waitFor(() => expect(screen.getByText('写入正史前确认')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled();

    resolveConsistency({
      chapter_id: 11,
      draft_version: 2,
      selected_change_indexes: { characters: [0], foreshadows: [] },
      consistency_summary: { status: 'blocked', total: 1, info_count: 0, warning_count: 0, blocking_count: 1 },
      consistency_warnings: [
        { severity: 'blocking', category: 'stale_result', message: '迟到的一致性结果不应覆盖当前视图。', object_type: 'foreshadow', object_id: 1, change_index: 0, details: {} },
      ],
    });

    await waitFor(() => expect(screen.queryByText('迟到的一致性结果不应覆盖当前视图。')).not.toBeInTheDocument());
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled();
  });

  it('keeps approval closed when consistency validation for the current selection fails', async () => {
    approvalPanelVersion.current = 1;
    const user = userEvent.setup();
    vi.mocked(checkApprovalConsistency).mockRejectedValueOnce(new Error('一致性检查暂时失败'));
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(await screen.findByRole('checkbox', { name: /伏笔：裂纹玉佩/ }));

    expect(await screen.findByRole('alert')).toHaveTextContent('一致性检查暂时失败');
    const approveButton = screen.getByRole('button', { name: '写入正史并更新世界' });
    expect(approveButton).toBeDisabled();
    await user.click(approveButton);
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('keeps approval closed when consistency response belongs to another draft version', async () => {
    const user = userEvent.setup();
    vi.mocked(checkApprovalConsistency).mockResolvedValueOnce({
      chapter_id: 11,
      draft_version: 2,
      selected_change_indexes: { characters: [0], foreshadows: [] },
      consistency_summary: { status: 'clear', total: 0, info_count: 0, warning_count: 0, blocking_count: 0 },
      consistency_warnings: [],
    });
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(await screen.findByRole('checkbox', { name: /伏笔：裂纹玉佩/ }));

    expect(await screen.findByRole('alert')).toHaveTextContent('一致性检查版本不一致：当前草稿为 v1，返回为 v2。请重试。');
    const approveButton = screen.getByRole('button', { name: '写入正史并更新世界' });
    expect(approveButton).toBeDisabled();
    await user.click(approveButton);
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('keeps the current review panels when switching draft versions fails', async () => {
    approvalPanelVersion.current = 2;
    const user = userEvent.setup();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.type(await screen.findByLabelText('修订指令'), '补足林砚试探沈微霜的过程');
    await user.click(screen.getByRole('button', { name: '生成修订版' }));

    expect(await screen.findByText('写入正史前确认')).toBeInTheDocument();
    expect(screen.getByText('Approval Readiness')).toBeInTheDocument();
    vi.mocked(getDraftVersion).mockRejectedValueOnce(new Error('版本读取失败'));

    await user.selectOptions(screen.getByLabelText('草稿版本'), '1');

    expect(await screen.findByRole('alert')).toHaveTextContent('版本读取失败');
    expect(screen.getByLabelText('草稿版本')).toHaveValue('2');
    expect(screen.getByText('写入正史前确认')).toBeInTheDocument();
    expect(screen.getByText('Approval Readiness')).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /角色：林砚/ })).toBeEnabled();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled();
  });

  it('renders approval preview changes as selected checkboxes by default', async () => {
    const user = userEvent.setup();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

    expect(await screen.findByRole('checkbox', { name: /角色：林砚/ })).toBeChecked();
    expect(screen.getByRole('checkbox', { name: /伏笔：裂纹玉佩/ })).toBeChecked();
    expect(screen.getByText('已选择 2 / 2 条拟提交变化')).toBeInTheDocument();
  });

  it('submits only selected approval change indexes with the current draft version', async () => {
    approvalPanelVersion.current = 1;
    const user = userEvent.setup();
    const onApproved = vi.fn();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={onApproved} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(await screen.findByRole('checkbox', { name: /伏笔：裂纹玉佩/ }));
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));

    expect(checkApprovalConsistency).toHaveBeenCalledWith(11, {
      draft_version: 1,
      selected_character_change_indexes: [0],
      selected_foreshadow_change_indexes: [],
    });
    expect(approveChapter).toHaveBeenCalledWith(11, {
      draft_version: 1,
      selected_character_change_indexes: [0],
      selected_foreshadow_change_indexes: [],
    });
  });

  it('does not resubmit approval when settlement loading fails after canon commit', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest)
      .mockRejectedValueOnce(new Error('世界概览暂不可用'))
      .mockResolvedValueOnce(approvedWorld);
    renderResumedStudio();

    await waitFor(() => expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('正史已提交，但世界结算加载失败：世界概览暂不可用');
    expect(alert).toHaveTextContent('本章不会再次提交写入');
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '编辑正文' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '驳回' })).toBeDisabled();
    expect(approveChapter).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: '重试加载世界结算' }));

    expect(await screen.findByText('世界推进结算')).toBeInTheDocument();
    expect(apiRequest).toHaveBeenCalledTimes(2);
    expect(approveChapter).toHaveBeenCalledTimes(1);
    expect(getChapterHistoryDetail).not.toHaveBeenCalled();
  });

  it('reconciles an unknown approval result before loading settlement without resubmitting canon', async () => {
    const user = userEvent.setup();
    vi.mocked(approveChapter).mockRejectedValueOnce(Object.assign(new Error('网关暂不可用'), { status: 503 }));
    vi.mocked(apiRequest).mockResolvedValueOnce(approvedWorld);
    renderResumedStudio();

    await waitFor(() => expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));

    expect(await screen.findByText(/正史写入请求的结果暂时未知/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '编辑正文' })).toBeDisabled();
    expect(approveChapter).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: '核对正史写入结果' }));

    expect(getChapterHistoryDetail).toHaveBeenCalledWith(11);
    expect(await screen.findByText('世界推进结算')).toBeInTheDocument();
    expect(approveChapter).toHaveBeenCalledTimes(1);
  });

  it('reopens approval only after reconciliation confirms the chapter is not approved', async () => {
    const user = userEvent.setup();
    vi.mocked(approveChapter).mockRejectedValueOnce(Object.assign(new Error('网关暂不可用'), { status: 503 }));
    vi.mocked(getChapterHistoryDetail).mockRejectedValueOnce(Object.assign(new Error('CHAPTER_NOT_APPROVED'), { status: 409 }));
    renderResumedStudio();

    await waitFor(() => expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));
    await user.click(await screen.findByRole('button', { name: '核对正史写入结果' }));

    expect(await screen.findByText(/服务器确认本章尚未写入正史/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled());
    expect(getApprovalPreview).toHaveBeenCalledTimes(2);
    expect(getApprovalReadiness).toHaveBeenCalledTimes(2);
    expect(approveChapter).toHaveBeenCalledTimes(1);
  });

  it('invalidates stale approval checks after a server-side version conflict', async () => {
    const user = userEvent.setup();
    const conflict = Object.assign(new Error('WORLD_VERSION_MISMATCH'), { status: 409 });
    vi.mocked(approveChapter).mockRejectedValueOnce(conflict);
    renderResumedStudio();

    await waitFor(() => expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));

    expect(await screen.findByText('WORLD_VERSION_MISMATCH')).toBeInTheDocument();
    expect(screen.getByText(/草稿或世界版本可能已变化/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
    expect(approveChapter).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: '重试审批检查' }));

    await waitFor(() => expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeEnabled());
    expect(getApprovalPreview).toHaveBeenCalledTimes(2);
    expect(getApprovalReadiness).toHaveBeenCalledTimes(2);
    expect(approveChapter).toHaveBeenCalledTimes(1);
  });

  it('renders a recovered approval settlement as read-only without calling approval or review APIs', async () => {
    render(
      <StudioPage
        world={approvedWorld}
        launchContext={{
          recentApproval: {
            chapter_id: 11,
            title: '第一章 雨巷密谈',
            approved_version: 1,
            world_version_before: 1,
            world_version_after: 2,
            character_change_count: 1,
            foreshadow_change_count: 1,
          },
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    expect(screen.getByText('世界推进结算')).toBeInTheDocument();
    expect(screen.getByText('世界进度第 1 版 → 第 2 版')).toBeInTheDocument();
    expect(screen.queryByLabelText('章节目标')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '创建章节' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '写入正史并更新世界' })).not.toBeInTheDocument();
    expect(approveChapter).not.toHaveBeenCalled();
    expect(getApprovalPreview).not.toHaveBeenCalled();
    expect(getApprovalReadiness).not.toHaveBeenCalled();
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('opens a fresh chapter workspace only after continuing from a recovered settlement', async () => {
    const user = userEvent.setup();
    render(
      <StudioPage
        world={approvedWorld}
        launchContext={{
          recentApproval: {
            chapter_id: 11,
            title: '第一章 雨巷密谈',
            approved_version: 1,
            world_version_before: 1,
            world_version_after: 2,
            character_change_count: 1,
            foreshadow_change_count: 1,
          },
        }}
        onBack={vi.fn()}
        onApproved={vi.fn()}
      />,
    );

    await user.click(screen.getByRole('button', { name: '继续下一章' }));

    expect(screen.queryByText('世界推进结算')).not.toBeInTheDocument();
    expect(screen.getByLabelText('章节目标')).toHaveValue('');
    expect(screen.getByRole('button', { name: '创建章节' })).toBeEnabled();
    expect(approveChapter).not.toHaveBeenCalled();
  });

  it('shows world progression settlement after approval before returning to overview', async () => {
    const user = userEvent.setup();
    const onApproved = vi.fn();
    vi.mocked(apiRequest).mockResolvedValueOnce(approvedWorld);
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={onApproved} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));

    expect(await screen.findByText('世界推进结算')).toBeInTheDocument();
    expect(onApproved).not.toHaveBeenCalled();
    expect(screen.getByText('世界进度第 1 版 → 第 2 版')).toBeInTheDocument();
    expect(screen.getByText('已写入正史章节：1')).toBeInTheDocument();
    expect(screen.getByText('角色变化：1')).toBeInTheDocument();
    expect(screen.getByText('悬念/伏笔变化：1')).toBeInTheDocument();
    expect(screen.getByText('已写入世界历史记录')).toBeInTheDocument();
    expect(screen.getByText('下一章将基于这些变化继续生成。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '继续下一章' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '查看世界概览' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '导出世界档案' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '查看世界概览' }));

    expect(onApproved).toHaveBeenCalledWith(approvedWorld);
  });

  it('exports the world archive from the settlement panel', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockResolvedValueOnce(approvedWorld);
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));
    await user.click(await screen.findByRole('button', { name: '导出世界档案' }));

    expect(exportWorldArchiveMarkdown).toHaveBeenCalledWith(7);
    expect(await screen.findByText('已导出世界档案：qinglan-v2.zip')).toBeInTheDocument();
  });

  it('continues with a fresh chapter session from the settlement panel', async () => {
    const user = userEvent.setup();
    vi.mocked(apiRequest).mockResolvedValueOnce(approvedWorld);
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));
    await user.click(await screen.findByRole('button', { name: '继续下一章' }));

    expect(screen.queryByText('世界推进结算')).not.toBeInTheDocument();
    // New workbench behavior: latest approved chapter is readable behind the fresh chapter workspace
    expect(await screen.findByText('正史正文')).toBeInTheDocument();
    expect(screen.getByLabelText('章节目标')).toHaveValue('');
    expect(screen.getByRole('button', { name: '创建章节' })).toBeEnabled();
    expect(screen.getByText('当前上下文')).toBeInTheDocument();
    expect(screen.getByText('世界进度：2')).toBeInTheDocument();
  });

  it('renders approval consistency warnings from the preview', async () => {
    const user = userEvent.setup();
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

    expect(await screen.findByText('设定冲突检查')).toBeInTheDocument();
    expect(screen.getByText('存在需复核项')).toBeInTheDocument();
    expect(screen.getByText('角色「林砚」的状态与目标同时大幅变化，请确认正文已有足够铺垫。')).toBeInTheDocument();
  });

  it('disables approval when selected consistency is blocked', async () => {
    const user = userEvent.setup();
    vi.mocked(checkApprovalConsistency).mockResolvedValueOnce({
      chapter_id: 11,
      draft_version: 1,
      selected_change_indexes: { characters: [0], foreshadows: [] },
      consistency_summary: { status: 'blocked', total: 1, info_count: 0, warning_count: 0, blocking_count: 1 },
      consistency_warnings: [
        { severity: 'blocking', category: 'foreshadow_transition', message: '伏笔「裂纹玉佩」不能从 resolved 回退到 advanced。', object_type: 'foreshadow', object_id: 1, change_index: 0, details: {} },
      ],
    });
    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(await screen.findByRole('checkbox', { name: /伏笔：裂纹玉佩/ }));

    expect(await screen.findByText('存在阻塞项')).toBeInTheDocument();
    expect(screen.getByText('伏笔「裂纹玉佩」不能从 resolved 回退到 advanced。')).toBeInTheDocument();
    expect(screen.getByText('存在阻塞项，请取消相关变化或重新修订草稿。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '写入正史并更新世界' })).toBeDisabled();
  });
});
