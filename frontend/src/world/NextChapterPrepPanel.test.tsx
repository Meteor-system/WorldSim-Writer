import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { NextChapterPrepResponse } from '../api/types';
import { NextChapterPrepPanel } from './NextChapterPrepPanel';

const prep: NextChapterPrepResponse = {
  world_id: 7,
  world_version: 2,
  next_chapter_number: 2,
  suggested_goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
  recommended_pov_character_id: 1,
  recommended_pov_character_name: '林砚',
  source_signals: ['character_arc_progression_hint', 'story_arc'],
  priority_characters: [
    {
      character_id: 1,
      name: '林砚',
      role_type: 'protagonist',
      status: '开始调查密信',
      reason: '上一章 progression hint 建议让该角色推动下一章。',
    },
  ],
  priority_foreshadows: [
    {
      foreshadow_id: 1,
      title: '裂纹玉佩',
      status: 'advanced',
      urgency_level: 4,
      reason: '该伏笔与上一章 progression hint 相关。',
    },
  ],
  progression_hints: [
    {
      hint_type: 'character',
      priority: 'high',
      title: '试探沈微霜是否可信',
      rationale: '上一章已经建立湿信线索。',
      suggested_next_beat: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      related_character_ids: [1],
      related_foreshadow_ids: [1],
      can_seed_next_chapter_goal: true,
    },
  ],
  continuity_warnings: [
    {
      severity: 'medium',
      category: 'character_arc',
      message: '下一章需要补足试探过程。',
      related_character_ids: [1],
      related_foreshadow_ids: [],
    },
  ],
  recent_events: [
    {
      id: 4,
      event_type: 'chapter_approved',
      world_version_before: 1,
      world_version_after: 2,
      payload: {},
      created_at: '2026-05-30T00:00:00Z',
    },
  ],
};

describe('NextChapterPrepPanel', () => {
  it('renders next chapter prep signals and uses suggested goal callback', async () => {
    const user = userEvent.setup();
    const onUseContext = vi.fn();
    const onEnterStudioWithContext = vi.fn();

    render(<NextChapterPrepPanel prep={prep} onUseContext={onUseContext} onEnterStudioWithContext={onEnterStudioWithContext} />);

    expect(screen.getByText('下一章准备台')).toBeInTheDocument();
    expect(screen.getByText('第 2 章建议目标')).toBeInTheDocument();
    expect(screen.getByText('林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
    expect(screen.getByText('推荐 POV：林砚')).toBeInTheDocument();
    expect(screen.getByText('林砚 · protagonist')).toBeInTheDocument();
    expect(screen.getByText('裂纹玉佩 · advanced · urgency 4')).toBeInTheDocument();
    expect(screen.getByText('试探沈微霜是否可信')).toBeInTheDocument();
    expect(screen.getByText('下一章需要补足试探过程。')).toBeInTheDocument();
    expect(screen.getByText('chapter_approved · 世界 1 → 2')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '用作下一章目标' }));
    expect(onUseContext).toHaveBeenCalledWith(expect.objectContaining({
      source: 'next_chapter_prep',
      goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      recommended_pov: { character_id: 1, name: '林砚' },
    }));

    await user.click(screen.getByRole('button', { name: '进入创作台并使用此目标' }));
    expect(onEnterStudioWithContext).toHaveBeenCalledWith(expect.objectContaining({
      source: 'next_chapter_prep',
      goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
    }));
  });

  it('renders loading and error states', () => {
    const { rerender } = render(<NextChapterPrepPanel prep={null} loading={true} />);
    expect(screen.getByRole('status')).toHaveTextContent('正在加载下一章准备台');

    rerender(<NextChapterPrepPanel prep={null} loading={false} error="下一章准备台暂不可用" />);
    expect(screen.getByRole('alert')).toHaveTextContent('下一章准备台暂不可用');
  });
});
