import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import type { WorldPulseResponse } from '../api/types';
import { WorldPulsePanel } from './WorldPulsePanel';

const pulse: WorldPulseResponse = {
  world_id: 7,
  world_version: 3,
  pulse_status: 'urgent',
  primary_mode: 'converge',
  headline: '世界近况：开放线索压力较高，建议下一章优先收束。',
  indicators: [
    { key: 'narrative_health', label: '叙事健康', value: '84/100 · watch', status: 'watch', detail: '来自叙事健康度的聚合风险。' },
    { key: 'open_threads', label: '开放线索', value: '3', status: 'risk', detail: '必须收束 1，建议推进 2。' },
  ],
  focus: [
    {
      focus_key: 'converge_threads',
      priority: 'urgent',
      title: '处理开放线索压力',
      detail: '开放线索 3 个，其中必须收束 1 个。',
      suggested_action: '查看开放线索看板。',
      related_thread_id: 'foreshadow:9',
    },
  ],
  next_actions: [
    { action_key: 'open_threads_board', label: '查看开放线索看板', detail: '选择最高压开放线索。', target: 'open_threads' },
  ],
  source_summary: { approved_chapter_count: 2 },
};

afterEach(() => cleanup());

describe('WorldPulsePanel', () => {
  it('renders headline, status, mode, indicators, focus, and actions', () => {
    render(<WorldPulsePanel pulse={pulse} loading={false} error="" />);

    expect(screen.getByText('世界近况')).toBeInTheDocument();
    expect(screen.getByText('世界近况：开放线索压力较高，建议下一章优先收束。')).toBeInTheDocument();
    expect(screen.getByText('状态：紧急')).toBeInTheDocument();
    expect(screen.getByText('模式：叙事收束')).toBeInTheDocument();
    expect(screen.getByText('叙事健康')).toBeInTheDocument();
    expect(screen.getByText('开放线索')).toBeInTheDocument();
    expect(screen.getByText('处理开放线索压力')).toBeInTheDocument();
    expect(screen.getByText('查看开放线索看板')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    render(<WorldPulsePanel pulse={null} loading={false} error="" />);

    expect(screen.getByText('世界近况暂无数据。')).toBeInTheDocument();
  });

  it('renders loading and error states', () => {
    const { rerender } = render(<WorldPulsePanel pulse={null} loading error="" />);
    expect(screen.getByRole('status')).toHaveTextContent('正在读取世界近况...');

    rerender(<WorldPulsePanel pulse={null} loading={false} error="pulse down" />);
    expect(screen.getByRole('alert')).toHaveTextContent('pulse down');
  });
});
