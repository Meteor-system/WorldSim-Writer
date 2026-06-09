import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import type { ArcPlanResponse } from '../api/types';
import { ArcPlanPanel } from './ArcPlanPanel';

const arcPlan: ArcPlanResponse = {
  world_id: 7,
  world_version: 4,
  arc_mode: 'converge',
  mode_reason: '开放线索压力过高，下一章应优先收束旧承诺。',
  expansion_budget: 'locked',
  next_chapter_number: 5,
  recommended_goal: '回收黑匣子脉冲，并让许砚做出阶段性选择。',
  closure_items: [
    {
      item_key: 'closure:foreshadow:9',
      thread_id: 'foreshadow:9',
      treatment: 'close',
      priority: 'must_close',
      title: '黑匣子脉冲',
      rationale: '超过建议回收窗口，请优先推进或收束。',
      suggested_next_step: '下一章优先回收该伏笔。',
      related_character_ids: [1, 2],
      related_foreshadow_ids: [9],
    },
  ],
  guidance: [
    { guidance_key: 'close_old_promises', label: '优先兑现旧承诺', detail: '减少新增谜团。' },
  ],
  source_summary: { must_close_count: 1 },
};

afterEach(() => cleanup());

describe('ArcPlanPanel', () => {
  it('renders mode, budget, goal, guidance, and closure items', () => {
    render(<ArcPlanPanel arcPlan={arcPlan} loading={false} error="" />);

    expect(screen.getByText('篇章收束计划')).toBeInTheDocument();
    expect(screen.getByText('叙事阶段：收束旧线索')).toBeInTheDocument();
    expect(screen.getByText('开放新线索：暂停新增')).toBeInTheDocument();
    expect(screen.getByText('开放线索压力过高，下一章应优先收束旧承诺。')).toBeInTheDocument();
    expect(screen.getByText('第 5 章建议目标')).toBeInTheDocument();
    expect(screen.getByText('回收黑匣子脉冲，并让许砚做出阶段性选择。')).toBeInTheDocument();
    expect(screen.getByText('优先兑现旧承诺')).toBeInTheDocument();
    expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
    expect(screen.getByText('处理方式：本章收束 · 优先级：必须处理')).toBeInTheDocument();
    expect(screen.getByText('线索来源：伏笔线索')).toBeInTheDocument();
    expect(screen.getByText('关联角色：2 位')).toBeInTheDocument();
    expect(screen.getByText('关联伏笔：1 条')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('Arc Mode / Closure Plan');
    expect(document.body).not.toHaveTextContent('模式：converge');
    expect(document.body).not.toHaveTextContent('扩张预算：locked');
    expect(document.body).not.toHaveTextContent('close · must_close');
    expect(document.body).not.toHaveTextContent('foreshadow:9');
    expect(document.body).not.toHaveTextContent('关联伏笔：9');
    expect(document.body).not.toHaveTextContent('关联角色：1、2');
  });

  it('renders empty state', () => {
    render(<ArcPlanPanel arcPlan={null} loading={false} error="" />);

    expect(screen.getByText('篇章模式与收束计划暂无数据。')).toBeInTheDocument();
  });

  it('renders loading and error states', () => {
    const { rerender } = render(<ArcPlanPanel arcPlan={null} loading error="" />);
    expect(screen.getByRole('status')).toHaveTextContent('正在读取篇章模式...');

    rerender(<ArcPlanPanel arcPlan={null} loading={false} error="arc plan down" />);
    expect(screen.getByRole('alert')).toHaveTextContent('arc plan down');
  });
});
