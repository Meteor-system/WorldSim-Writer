import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import type { OpenThreadsResponse } from '../api/types';
import { OpenThreadsPanel } from './OpenThreadsPanel';

const openThreads: OpenThreadsResponse = {
  world_id: 7,
  world_version: 3,
  summary: {
    total_open_threads: 2,
    must_close_count: 1,
    should_advance_count: 1,
    can_delay_count: 0,
    can_leave_open_count: 0,
    convergence_ratio: 0.25,
    narrative_entropy_level: 'medium',
    recent_event_count: 4,
  },
  threads: [
    {
      thread_id: 'health_risk:critic:0',
      thread_type: 'health_risk',
      priority: 'must_close',
      pressure_level: 'high',
      title: '第一章 灯塔密令',
      summary: '开头缺少抓力。',
      related_object_type: 'chapter',
      related_object_id: 11,
      related_character_ids: [],
      related_foreshadow_ids: [],
      suggested_action: '优先修订最近章节。',
      can_seed_next_chapter_goal: true,
    },
    {
      thread_id: 'foreshadow:9',
      thread_type: 'foreshadow',
      priority: 'should_advance',
      pressure_level: 'high',
      title: '黑匣子脉冲',
      summary: '高紧迫度：5',
      related_object_type: 'foreshadow',
      related_object_id: 9,
      related_character_ids: [1],
      related_foreshadow_ids: [9],
      suggested_action: '下一章推进该伏笔。',
      can_seed_next_chapter_goal: true,
    },
  ],
  suggested_next_actions: [
    { action_key: 'seed_next_chapter_goal', label: '用最高压开放线索规划下一章', detail: '优先修订最近章节。' },
  ],
};

afterEach(() => cleanup());

describe('OpenThreadsPanel', () => {
  it('renders convergence summary, thread cards, and actions', () => {
    render(<OpenThreadsPanel openThreads={openThreads} loading={false} error="" />);

    expect(screen.getByText('Open Threads Board')).toBeInTheDocument();
    expect(screen.getByText('开放线索：2')).toBeInTheDocument();
    expect(screen.getByText('必须收束：1')).toBeInTheDocument();
    expect(screen.getByText('收束比：25%')).toBeInTheDocument();
    expect(screen.getByText('叙事熵：medium')).toBeInTheDocument();
    expect(screen.getByText('第一章 灯塔密令')).toBeInTheDocument();
    expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
    expect(screen.getByText('[must_close] health_risk · high')).toBeInTheDocument();
    expect(screen.getAllByText('可作为下一章目标种子').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('用最高压开放线索规划下一章')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    render(<OpenThreadsPanel openThreads={{ ...openThreads, summary: { ...openThreads.summary, total_open_threads: 0 }, threads: [], suggested_next_actions: [] }} loading={false} error="" />);

    expect(screen.getByText('当前没有需要优先处理的开放线索。')).toBeInTheDocument();
  });

  it('renders loading and error states', () => {
    const { rerender } = render(<OpenThreadsPanel openThreads={null} loading error="" />);
    expect(screen.getByRole('status')).toHaveTextContent('正在加载开放线索...');

    rerender(<OpenThreadsPanel openThreads={null} loading={false} error="threads down" />);
    expect(screen.getByRole('alert')).toHaveTextContent('threads down');
  });
});
