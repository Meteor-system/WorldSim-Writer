import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { DraftResponse, WorldOverview } from '../api/types';
import { StudioPage } from './StudioPage';

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

describe('StudioPage Review Studio 2.0 controls', () => {
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
  });
});
