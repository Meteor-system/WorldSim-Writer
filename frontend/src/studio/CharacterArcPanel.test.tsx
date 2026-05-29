import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import type { CharacterArcReportResponse } from '../api/types';
import { CharacterArcPanel } from './CharacterArcPanel';

const report: CharacterArcReportResponse = {
  chapter_id: 11,
  draft_version: 1,
  current_draft_version: 2,
  is_stale: true,
  summary: '本章推动林砚从被动等待转向主动追查湿信来源。',
  character_arcs: [
    {
      character_id: 1,
      name: '林砚',
      role_type: 'protagonist',
      current_status: 'active',
      current_goals: [],
      presence_level: 'major',
      arc_stage: 'choice',
      chapter_function: '在雨巷会面中承担调查者与选择者功能。',
      observed_shift: '从谨慎观察转向主动追问湿信来源。',
      proposed_state_change: { status: '开始调查密信', current_goals: ['追查湿信来源'] },
      continuity_risk: 'high',
      risk_reason: '如果立刻信任沈微霜，需要补足信任建立过程。',
      suggested_revision: '增加林砚犹疑和试探沈微霜的动作。',
      next_chapter_setup: '让林砚以湿信为线索试探城主府密道。',
    },
  ],
  relationship_notes: [
    {
      source_character_id: 1,
      target_character_id: 2,
      source_name: '林砚',
      target_name: '沈微霜',
      relation_type: 'uneasy_ally',
      current_intensity: 3,
      visibility: 'private',
      chapter_shift: '从戒备转向有限交换情报。',
      progression_hint: '下一章让两人通过一次试探建立最低限度合作。',
      risk_level: 'medium',
      risk_reason: '信任升温略快。',
    },
  ],
  progression_hints: [
    {
      hint_type: 'character',
      priority: 'high',
      title: '让林砚做出是否相信沈微霜的选择',
      rationale: '本章已经建立湿信线索，下一章需要把怀疑转化为行动。',
      suggested_next_beat: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      related_character_ids: [1],
      related_foreshadow_ids: [1],
      can_seed_next_chapter_goal: true,
    },
  ],
  created_at: '2026-05-29T00:00:00Z',
};

describe('CharacterArcPanel', () => {
  it('renders stale warning, character arcs, relationship notes, and progression hints', async () => {
    const user = userEvent.setup();
    const onUseHintAsGoal = vi.fn();

    render(<CharacterArcPanel report={report} working={false} onUseHintAsGoal={onUseHintAsGoal} />);

    expect(screen.getByText('角色弧线报告')).toBeInTheDocument();
    expect(screen.getByText('本章推动林砚从被动等待转向主动追查湿信来源。')).toBeInTheDocument();
    expect(screen.getByText('报告来自 v1，当前草稿为 v2，请重新生成。')).toBeInTheDocument();
    expect(screen.getByText('林砚 · protagonist')).toBeInTheDocument();
    expect(screen.getByText('出现：major · 阶段：choice')).toBeInTheDocument();
    expect(screen.getByText('连续性高风险：如果立刻信任沈微霜，需要补足信任建立过程。')).toBeInTheDocument();
    expect(screen.getByText('林砚 → 沈微霜 · uneasy_ally')).toBeInTheDocument();
    expect(screen.getByText('让林砚做出是否相信沈微霜的选择')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '用作下一章目标' }));

    expect(onUseHintAsGoal).toHaveBeenCalledWith('林砚带着湿信赴城主府外墙，并设置一次试探。');
  });
});
