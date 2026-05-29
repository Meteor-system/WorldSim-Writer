import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { CriticReportResponse } from '../api/types';
import { CriticReportPanel } from './CriticReportPanel';

const report: CriticReportResponse = {
  chapter_id: 11,
  draft_version: 1,
  current_draft_version: 2,
  is_stale: true,
  overall_score: 78,
  summary: '章节冲突清晰，但第二段信息揭示偏快，对白可更有潜台词。',
  dimensions: {
    pacing: {
      score: 72,
      summary: '中段推进略快。',
      issues: [],
      suggestions: ['放慢第二段的信息揭示。'],
    },
    tension: {
      score: 82,
      summary: '雨巷会面有悬念。',
      issues: [],
      suggestions: ['让信件内容更晚揭示。'],
    },
    character_consistency: {
      score: 85,
      summary: '林砚目标与当前状态一致。',
      issues: [],
      suggestions: ['保留林砚的谨慎反应。'],
    },
    dialogue_quality: {
      score: 68,
      summary: '对白略偏解释性。',
      issues: [],
      suggestions: ['减少直白解释。'],
    },
    structure: {
      score: 80,
      summary: '开端清晰。',
      issues: [],
      suggestions: ['章末保留更强钩子。'],
    },
    world_continuity: {
      score: 90,
      summary: '未发现世界观冲突。',
      issues: [],
      suggestions: ['保持伏笔推进与玉佩线索一致。'],
    },
    readability: {
      score: 76,
      summary: '可读性良好。',
      issues: [],
      suggestions: ['压缩重复意象。'],
    },
  },
  issues: [
    {
      severity: 'high',
      dimension: 'character_consistency',
      message: '林砚突然信任沈微霜，与当前谨慎状态冲突。',
      paragraph_index: 0,
      suggested_action: '重写相关段落，补足信任建立过程。',
    },
    {
      severity: 'medium',
      dimension: 'dialogue_quality',
      message: '第二段对白解释性较强。',
      paragraph_index: 1,
      suggested_action: '润色本段对白，增加潜台词。',
    },
  ],
  suggestions: ['优先修订第一段人物动机，再润色第二段对白。'],
  created_at: '2026-05-29T00:00:00Z',
};

describe('CriticReportPanel', () => {
  it('renders score cards, stale warning, issue actions, and high-severity approval warning', async () => {
    const user = userEvent.setup();
    const onReviseParagraph = vi.fn();

    render(<CriticReportPanel report={report} working={false} onReviseParagraph={onReviseParagraph} />);

    expect(screen.getByText('Critic 报告')).toBeInTheDocument();
    expect(screen.getByText('总评分：78/100')).toBeInTheDocument();
    expect(screen.getByText('报告来自 v1，当前草稿为 v2，请重新生成。')).toBeInTheDocument();
    expect(screen.getByText('Critic 发现高风险问题，建议修订后再批准。')).toBeInTheDocument();
    expect(screen.getByText('节奏')).toBeInTheDocument();
    expect(screen.getByText('对白质量')).toBeInTheDocument();
    expect(screen.getByText('世界观/伏笔一致性')).toBeInTheDocument();
    expect(screen.getByText('[high] 人物一致性 · 第 1 段')).toBeInTheDocument();
    expect(screen.getByText('林砚突然信任沈微霜，与当前谨慎状态冲突。')).toBeInTheDocument();
    expect(screen.getByText('优先修订第一段人物动机，再润色第二段对白。')).toBeInTheDocument();

    await user.click(screen.getAllByRole('button', { name: '重写相关段落' })[0]);
    await user.click(screen.getAllByRole('button', { name: '润色相关段落' })[1]);

    expect(onReviseParagraph).toHaveBeenNthCalledWith(1, 0, 'rewrite');
    expect(onReviseParagraph).toHaveBeenNthCalledWith(2, 1, 'polish');
  });
});
