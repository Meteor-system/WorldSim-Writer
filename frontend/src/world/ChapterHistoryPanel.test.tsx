import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ApprovedChapterHistoryDetailResponse, ApprovedChapterHistoryResponse } from '../api/types';
import { ChapterHistoryPanel } from './ChapterHistoryPanel';

const history: ApprovedChapterHistoryResponse = {
  world_id: 7,
  chapters: [
    {
      id: 11,
      title: '第一章 雨巷密谈',
      status: 'approved',
      approved_version: 2,
      base_world_version: 1,
      world_version_after: 2,
      approved_excerpt: '林砚停在雨巷口，掌心玉佩微微发烫。',
      event_count: 4,
      character_change_count: 1,
      foreshadow_change_count: 1,
    },
  ],
};

const detail: ApprovedChapterHistoryDetailResponse = {
  id: 11,
  world_id: 7,
  title: '第一章 雨巷密谈',
  status: 'approved',
  approved_version: 2,
  base_world_version: 1,
  approved_content: '林砚停在雨巷口，掌心玉佩微微发烫。\n\n沈微霜递来一封湿透的信。',
  world_version_before: 1,
  world_version_after: 2,
  events: [
    {
      id: 1,
      event_type: 'chapter_approved',
      source_type: 'chapter_approval',
      world_version_before: 1,
      world_version_after: 2,
      payload: { chapter_title: '第一章 雨巷密谈' },
      created_at: '2026-05-30T00:00:00Z',
    },
  ],
  character_changes: [
    {
      event_type: 'character_change',
      object_type: 'character',
      object_id: 1,
      before: { status: 'active' },
      after: { status: '开始调查密信', current_goals: ['追查湿信来源'] },
      payload: {},
    },
  ],
  foreshadow_changes: [
    {
      event_type: 'foreshadow_change',
      object_type: 'foreshadow',
      object_id: 1,
      before: { status: 'planted' },
      after: { status: 'advanced' },
      payload: {},
    },
  ],
  critic_summary: '章节冲突清晰，但第二段信息揭示偏快。',
  character_arc_summary: '本章推动林砚从被动等待转向主动追查。',
  execution_context: {
    source: 'next_chapter_prep',
    source_world_version: 2,
    next_chapter_number: 2,
    goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
    recommended_pov: { character_id: 1, name: '林砚' },
    source_signals: ['character_arc_progression_hint'],
    priority_characters: [{ character_id: 1, name: '林砚', role_type: 'protagonist', status: '开始调查密信', reason: '上一章提示。' }],
    priority_foreshadows: [{ foreshadow_id: 1, title: '裂纹玉佩', status: 'advanced', urgency_level: 4, reason: '该伏笔需要推进。' }],
    progression_hints: [],
    continuity_warnings: [{ severity: 'medium', category: 'character_arc', message: '下一章需要补足试探过程。', related_character_ids: [1], related_foreshadow_ids: [] }],
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
  },
};

afterEach(() => cleanup());

describe('ChapterHistoryPanel', () => {
  it('renders approved chapter list and loads detail view with changes', async () => {
    const user = userEvent.setup();
    const onLoadDetail = vi.fn(async () => detail);

    render(<ChapterHistoryPanel history={history} loading={false} onLoadDetail={onLoadDetail} />);

    expect(screen.getByText('章节历史')).toBeInTheDocument();
    expect(screen.getByText('已批准章节历史')).toBeInTheDocument();
    expect(screen.getByText('第一章 雨巷密谈 · 批准稿第 2 版 · 世界第 1 版 → 第 2 版')).toBeInTheDocument();
    expect(screen.getByText('角色变化 1')).toBeInTheDocument();
    expect(screen.getByText('伏笔变化 1')).toBeInTheDocument();
    expect(screen.getByText('林砚停在雨巷口，掌心玉佩微微发烫。')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '查看详情' }));

    expect(onLoadDetail).toHaveBeenCalledWith(11);
    expect(await screen.findByText('章节详情')).toBeInTheDocument();
    expect(screen.getByText('第一章 雨巷密谈 · 批准稿第 2 版')).toBeInTheDocument();
    expect(screen.getByText('世界进度：第 1 版 → 第 2 版')).toBeInTheDocument();
    expect(screen.getByText('林砚停在雨巷口，掌心玉佩微微发烫。')).toBeInTheDocument();
    expect(screen.getByText('审批结算说明')).toBeInTheDocument();
    expect(screen.getByText('候选素材写作参考')).toBeInTheDocument();
    expect(screen.getByText('雨夜审讯（来源：旧设定.md）')).toBeInTheDocument();
    expect(screen.getByText('雨夜审讯从一盏坏灯开始。')).toBeInTheDocument();
    expect(screen.getByText('这些候选素材只是本章创作参考，不代表已自动进入正式设定。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('正式 canon');
    expect(document.body).not.toHaveTextContent('asset_id');
    expect(document.body).not.toHaveTextContent('batch_id');
    expect(document.body).not.toHaveTextContent('inspiration');
    expect(document.body).not.toHaveTextContent('markdown');
    expect(screen.getByText('正式事件：章节已批准并写入世界历史。')).toBeInTheDocument();
    expect(screen.getByText('正式结算：角色变化 1 条，伏笔变化 1 条。')).toBeInTheDocument();
    expect(screen.getByText('角色变化')).toBeInTheDocument();
    expect(screen.getByText('角色：林砚')).toBeInTheDocument();
    expect(screen.getByText('状态：进行中 → 开始调查密信')).toBeInTheDocument();
    expect(screen.getByText('目标：追查湿信来源')).toBeInTheDocument();
    expect(screen.getByText('伏笔变化')).toBeInTheDocument();
    expect(screen.getByText('伏笔：裂纹玉佩')).toBeInTheDocument();
    expect(screen.getByText('状态：已埋下 → 推进中')).toBeInTheDocument();
    expect(screen.getByText('正式事件')).toBeInTheDocument();
    expect(screen.queryByText('chapter_approved · 世界 1 → 2')).not.toBeInTheDocument();
    expect(screen.queryByText(/character_change · character #1/)).not.toBeInTheDocument();
    expect(screen.queryByText(/foreshadow_change · foreshadow #1/)).not.toBeInTheDocument();
    expect(screen.getByText('编辑建议：章节冲突清晰，但第二段信息揭示偏快。')).toBeInTheDocument();
    expect(screen.getByText('角色弧线：本章推动林砚从被动等待转向主动追查。')).toBeInTheDocument();
    expect(screen.getByText('写作依据快照')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('Approved Chapter History');
    expect(document.body).not.toHaveTextContent('Chapter Detail');
    expect(document.body).not.toHaveTextContent('第一章 雨巷密谈 · v2 · 世界 1 → 2');
    expect(document.body).not.toHaveTextContent('世界版本：1 → 2');
    expect(document.body).not.toHaveTextContent('状态：active → 开始调查密信');
    expect(document.body).not.toHaveTextContent('状态：planted → advanced');
    expect(document.body).not.toHaveTextContent('Critic：');
    expect(document.body).not.toHaveTextContent('执行上下文快照');
    expect(screen.getByText('目标：林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
    expect(screen.getByText('推荐 POV：林砚')).toBeInTheDocument();
    expect(screen.getByText('优先伏笔：裂纹玉佩')).toBeInTheDocument();
  });

  it('shows candidate-material empty state when chapter detail used no imported references', async () => {
    const user = userEvent.setup();
    const detailWithoutReferences: ApprovedChapterHistoryDetailResponse = {
      ...detail,
      execution_context: detail.execution_context
        ? { ...detail.execution_context, material_references: [] }
        : detail.execution_context,
    };
    const onLoadDetail = vi.fn(async () => detailWithoutReferences);

    render(<ChapterHistoryPanel history={history} loading={false} onLoadDetail={onLoadDetail} />);

    await user.click(screen.getByRole('button', { name: '查看详情' }));

    expect(await screen.findByText('章节详情')).toBeInTheDocument();
    expect(screen.getByText('本章未使用候选素材参考。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('本章未使用导入素材参考。');
    expect(document.body).not.toHaveTextContent('正式 canon');
    expect(document.body).not.toHaveTextContent('asset_id');
    expect(document.body).not.toHaveTextContent('batch_id');
    expect(document.body).not.toHaveTextContent('inspiration');
    expect(document.body).not.toHaveTextContent('markdown');
  });

  it('renders empty, loading, and error states', () => {
    const { rerender } = render(<ChapterHistoryPanel history={null} loading={true} onLoadDetail={vi.fn()} />);
    expect(screen.getByRole('status')).toHaveTextContent('正在加载章节历史');

    rerender(<ChapterHistoryPanel history={{ world_id: 7, chapters: [] }} loading={false} onLoadDetail={vi.fn()} />);
    expect(screen.getByText('还没有已批准章节。')).toBeInTheDocument();

    rerender(<ChapterHistoryPanel history={null} loading={false} error="章节历史暂不可用" onLoadDetail={vi.fn()} />);
    expect(screen.getByRole('alert')).toHaveTextContent('章节历史暂不可用');
  });
});
