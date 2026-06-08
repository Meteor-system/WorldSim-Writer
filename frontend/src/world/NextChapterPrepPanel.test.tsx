import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { NextChapterPrepResponse } from '../api/types';
import { NextChapterPrepPanel } from './NextChapterPrepPanel';

const prep: NextChapterPrepResponse = {
  world_id: 7,
  world_version: 2,
  next_chapter_number: 2,
  suggested_goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
  previous_chapter_summary: '林砚与沈微霜在雨巷交换湿信线索。',
  recommended_pov_character_id: 1,
  recommended_pov_character_name: '林砚',
  source_signals: ['character_arc_progression_hint', 'story_arc', 'import_material_reference'],
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
      reason: '高紧迫度：5；已埋设 6 章未推进',
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
};

afterEach(() => cleanup());

describe('NextChapterPrepPanel', () => {
  it('renders next chapter prep signals and uses suggested goal callback', async () => {
    const user = userEvent.setup();
    const onUseContext = vi.fn();
    const onEnterStudioWithContext = vi.fn();

    render(<NextChapterPrepPanel prep={prep} onUseContext={onUseContext} onEnterStudioWithContext={onEnterStudioWithContext} />);

    expect(screen.getByText('下一章写作准备')).toBeInTheDocument();
    expect(screen.getByText('下一章准备台')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('Next Chapter Prep');
    expect(screen.getByText('第 2 章建议目标')).toBeInTheDocument();
    expect(screen.getByText('林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
    expect(screen.getByText('上一章摘要')).toBeInTheDocument();
    expect(screen.getByText('林砚与沈微霜在雨巷交换湿信线索。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('previous_chapter_summary');
    expect(screen.getByText('候选素材参考')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('import_material_reference');
    expect(screen.getByText('推荐 POV：林砚')).toBeInTheDocument();
    expect(screen.getByText('林砚 · 主角')).toBeInTheDocument();
    expect(screen.getByText('裂纹玉佩 · 推进中 · 紧迫度 4')).toBeInTheDocument();
    expect(screen.getByText('理由：高紧迫度：5；已埋设 6 章未推进')).toBeInTheDocument();
    expect(screen.getByText('试探沈微霜是否可信')).toBeInTheDocument();
    expect(screen.getByText('下一章需要补足试探过程。')).toBeInTheDocument();
    expect(screen.getByText('章节写入正史 · 世界第 1 版 → 第 2 版')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('林砚 · protagonist');
    expect(document.body).not.toHaveTextContent('裂纹玉佩 · advanced · urgency 4');
    expect(document.body).not.toHaveTextContent('chapter_approved · 世界 1 → 2');
    expect(screen.getByText('候选素材写作参考')).toBeInTheDocument();
    expect(screen.getByText('雨夜审讯（来源：旧设定.md）')).toBeInTheDocument();
    expect(screen.getByText('雨夜审讯从一盏坏灯开始。')).toBeInTheDocument();
    expect(screen.getByText('这些候选素材只是下一章写作参考，不会自动改写正式设定。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('正式 canon');
    expect(document.body).not.toHaveTextContent('asset_id');
    expect(document.body).not.toHaveTextContent('batch_id');
    expect(document.body).not.toHaveTextContent('inspiration');

    await user.click(screen.getByRole('button', { name: '用作下一章目标' }));
    expect(onUseContext).toHaveBeenCalledWith(expect.objectContaining({
      source: 'next_chapter_prep',
      goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      recommended_pov: { character_id: 1, name: '林砚' },
      material_references: expect.arrayContaining([expect.objectContaining({ title: '雨夜审讯' })]),
    }));

    expect(screen.queryByRole('button', { name: '进入创作台并使用此目标' })).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '带下一章候选素材参考进入创作台' }));
    expect(onEnterStudioWithContext).toHaveBeenCalledWith(expect.objectContaining({
      source: 'next_chapter_prep',
      goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
    }));
  });

  it('keeps the generic studio CTA when no candidate references exist', () => {
    render(<NextChapterPrepPanel prep={{ ...prep, material_references: [] }} onEnterStudioWithContext={vi.fn()} />);

    expect(screen.getByRole('button', { name: '进入创作台并使用此目标' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '带下一章候选素材参考进入创作台' })).not.toBeInTheDocument();
    expect(screen.queryByText('候选素材写作参考')).not.toBeInTheDocument();
  });

  it('renders loading and error states', () => {
    const { rerender } = render(<NextChapterPrepPanel prep={null} loading={true} />);
    expect(screen.getByRole('status')).toHaveTextContent('正在加载下一章准备台');

    rerender(<NextChapterPrepPanel prep={null} loading={false} error="下一章准备台暂不可用" />);
    expect(screen.getByRole('alert')).toHaveTextContent('下一章准备台暂不可用');
  });
});
