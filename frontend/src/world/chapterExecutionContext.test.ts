import { describe, expect, it } from 'vitest';
import type { NextChapterPrepResponse, WorldOverview } from '../api/types';
import { buildExecutionContextFromPrep, buildManualExecutionContext, withEditedGoal } from './chapterExecutionContext';

const prep: NextChapterPrepResponse = {
  world_id: 7,
  world_version: 2,
  next_chapter_number: 2,
  suggested_goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
  recommended_pov_character_id: 1,
  recommended_pov_character_name: '林砚',
  source_signals: ['character_arc_progression_hint'],
  priority_characters: [
    { character_id: 1, name: '林砚', role_type: 'protagonist', status: '开始调查密信', reason: '上一章提示。' },
  ],
  priority_foreshadows: [
    { foreshadow_id: 1, title: '裂纹玉佩', status: 'advanced', urgency_level: 4, reason: '该伏笔需要推进。' },
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
    { severity: 'medium', category: 'character_arc', message: '下一章需要补足试探过程。', related_character_ids: [1], related_foreshadow_ids: [] },
  ],
  recent_events: [
    { id: 4, event_type: 'chapter_approved', world_version_before: 1, world_version_after: 2, payload: {}, created_at: '2026-05-30T00:00:00Z' },
  ],
};

const world = {
  id: 7,
  world_version: 3,
  approved_chapter_count: 2,
} as WorldOverview;

describe('chapterExecutionContext', () => {
  it('builds structured context from next chapter prep', () => {
    const context = buildExecutionContextFromPrep(prep);

    expect(context.source).toBe('next_chapter_prep');
    expect(context.source_world_version).toBe(2);
    expect(context.next_chapter_number).toBe(2);
    expect(context.goal).toBe(prep.suggested_goal);
    expect(context.recommended_pov.name).toBe('林砚');
    expect(context.priority_characters[0].reason).toBe('上一章提示。');
    expect(context.priority_foreshadows[0].title).toBe('裂纹玉佩');
    expect(context.progression_hints[0].title).toBe('试探沈微霜是否可信');
    expect(context.continuity_warnings[0].message).toBe('下一章需要补足试探过程。');
    expect(context.recent_events[0].event_type).toBe('chapter_approved');
  });

  it('builds manual context from world and goal', () => {
    const context = buildManualExecutionContext(world, '用户手动目标');

    expect(context.source).toBe('manual');
    expect(context.source_world_version).toBe(3);
    expect(context.next_chapter_number).toBe(3);
    expect(context.goal).toBe('用户手动目标');
    expect(context.source_signals).toEqual(['manual']);
    expect(context.priority_characters).toEqual([]);
  });

  it('applies edited goal to provided or manual context', () => {
    const context = buildExecutionContextFromPrep(prep);

    expect(withEditedGoal(context, world, '用户修改后的目标').goal).toBe('用户修改后的目标');
    expect(withEditedGoal(undefined, world, '无 NCC 的目标').source).toBe('manual');
  });
});
