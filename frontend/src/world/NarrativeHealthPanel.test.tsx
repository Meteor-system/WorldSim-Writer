import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import type { NarrativeHealthResponse } from '../api/types';
import { NarrativeHealthPanel } from './NarrativeHealthPanel';

const health: NarrativeHealthResponse = {
  world_id: 7,
  world_version: 3,
  health_score: 58,
  status: 'at_risk',
  summary: { approved_chapter_count: 1, high_risk_count: 1 },
  metrics: [
    { key: 'approved_chapters', label: '已批准章节', value: 1, status: 'ok', detail: '已正式写入世界历史的章节数量。' },
    { key: 'critic_issues', label: 'Critic 风险', value: 2, status: 'risk', detail: '高风险 1，中风险 1。' },
  ],
  risks: [
    {
      severity: 'high',
      source: 'critic',
      message: '开头缺少抓力。',
      object_type: 'chapter',
      object_id: 11,
      object_title: '第一章 灯塔密令',
      suggested_action: '修订最近章节或重新生成 Critic 报告。',
    },
  ],
  suggested_actions: [
    { action_key: 'revise_latest_chapter', label: '优先修订最近章节', detail: '存在高风险问题。' },
  ],
};

afterEach(() => cleanup());

describe('NarrativeHealthPanel', () => {
  it('renders score, metrics, risks, and actions', () => {
    render(<NarrativeHealthPanel health={health} loading={false} error="" />);

    expect(screen.getByText('Narrative Health')).toBeInTheDocument();
    expect(screen.getByText('58/100')).toBeInTheDocument();
    expect(screen.getByText('高风险')).toBeInTheDocument();
    expect(screen.getByText('Critic 风险')).toBeInTheDocument();
    expect(screen.getByText('开头缺少抓力。')).toBeInTheDocument();
    expect(screen.getByText('优先修订最近章节')).toBeInTheDocument();
  });

  it('renders no-risk state', () => {
    render(<NarrativeHealthPanel health={{ ...health, health_score: 92, status: 'healthy', risks: [] }} loading={false} error="" />);

    expect(screen.getByText('健康')).toBeInTheDocument();
    expect(screen.getByText('当前没有高风险叙事问题。')).toBeInTheDocument();
  });

  it('renders loading and error states', () => {
    const { rerender } = render(<NarrativeHealthPanel health={null} loading error="" />);
    expect(screen.getByRole('status')).toHaveTextContent('正在加载叙事健康度...');

    rerender(<NarrativeHealthPanel health={null} loading={false} error="health down" />);
    expect(screen.getByRole('alert')).toHaveTextContent('health down');
  });
});
