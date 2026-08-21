import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ConvergencePanel } from './ConvergencePanel';

vi.mock('../api/client', () => ({
  apiRequest: vi.fn(async () => ({
    world_id: 7,
    chapter_number: 2,
    total_planned_chapters: 20,
    arc_mode: 'pressure',
    arc_mode_label: '加压',
    entropy: 12,
    entropy_level: 'medium',
    entropy_message: '线索开始堆积',
    entropy_breakdown: {},
    open_threads: [],
    closure_plan: [{ title: '裂纹玉佩', urgency: 4, window: '第3-5章', recommended_chapter: 3, overdue: true, priority: 'P1' }],
  })),
  getConvergenceRatio: vi.fn(async () => ({ world_id: 7, opened_threads: 3, closed_threads: 1, merged_threads: 0, ratio: 0.33 })),
}));

afterEach(() => cleanup());

describe('ConvergencePanel', () => {
  it('fills an empty chapter goal from an overdue closure item', async () => {
    const user = userEvent.setup();
    const onUseGoal = vi.fn();
    render(<ConvergencePanel worldId={7} chapterGoal="" onUseGoal={onUseGoal} />);
    await user.click(await screen.findByRole('button', { name: '用作本章目标' }));
    expect(onUseGoal).toHaveBeenCalledWith('收束「裂纹玉佩」（建议第3章）');
  });

  it('does not overwrite a non-empty chapter goal', async () => {
    render(<ConvergencePanel worldId={7} chapterGoal="推进雨巷密谈" onUseGoal={vi.fn()} />);
    expect(await screen.findByRole('button', { name: '用作本章目标' })).toBeDisabled();
    expect(screen.getByText('章节目标非空，未覆盖。')).toBeInTheDocument();
  });
});
