import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
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
};

describe('ChapterHistoryPanel', () => {
  it('renders approved chapter list and loads detail view with changes', async () => {
    const user = userEvent.setup();
    const onLoadDetail = vi.fn(async () => detail);

    render(<ChapterHistoryPanel history={history} loading={false} onLoadDetail={onLoadDetail} />);

    expect(screen.getByText('章节历史')).toBeInTheDocument();
    expect(screen.getByText('第一章 雨巷密谈 · v2 · 世界 1 → 2')).toBeInTheDocument();
    expect(screen.getByText('角色变化 1')).toBeInTheDocument();
    expect(screen.getByText('伏笔变化 1')).toBeInTheDocument();
    expect(screen.getByText('林砚停在雨巷口，掌心玉佩微微发烫。')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '查看详情' }));

    expect(onLoadDetail).toHaveBeenCalledWith(11);
    expect(await screen.findByText('章节详情')).toBeInTheDocument();
    expect(screen.getByText('世界版本：1 → 2')).toBeInTheDocument();
    expect(screen.getByText('林砚停在雨巷口，掌心玉佩微微发烫。')).toBeInTheDocument();
    expect(screen.getByText('角色变化')).toBeInTheDocument();
    expect(screen.getByText(/开始调查密信/)).toBeInTheDocument();
    expect(screen.getByText('伏笔变化')).toBeInTheDocument();
    expect(screen.getByText(/advanced/)).toBeInTheDocument();
    expect(screen.getByText('正式事件')).toBeInTheDocument();
    expect(screen.getByText('chapter_approved · 世界 1 → 2')).toBeInTheDocument();
    expect(screen.getByText('Critic：章节冲突清晰，但第二段信息揭示偏快。')).toBeInTheDocument();
    expect(screen.getByText('角色弧线：本章推动林砚从被动等待转向主动追查。')).toBeInTheDocument();
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
