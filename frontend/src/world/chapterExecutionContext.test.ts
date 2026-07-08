import { describe, expect, it } from 'vitest';
import type { NextChapterPrepResponse, WorldOverview } from '../api/types';
import { buildExecutionContextFromPrep, buildManualExecutionContext, withEditedGoal, withStyleHandbookReference } from './chapterExecutionContext';

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
      created_at: '2026-06-03T00:00:00Z',
      safety_note: '导入素材参考只用于创作提示，不会自动改写正式 canon。',
    },
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
    expect(context.material_references[0].title).toBe('雨夜审讯');
  });

  it('builds manual context from world and goal', () => {
    const context = buildManualExecutionContext(world, '用户手动目标');

    expect(context.source).toBe('manual');
    expect(context.source_world_version).toBe(3);
    expect(context.next_chapter_number).toBe(3);
    expect(context.goal).toBe('用户手动目标');
    expect(context.source_signals).toEqual(['manual']);
    expect(context.priority_characters).toEqual([]);
    expect(context.material_references).toEqual([]);
  });

  it('applies edited goal to provided or manual context', () => {
    const context = buildExecutionContextFromPrep(prep);

    expect(withEditedGoal(context, world, '用户修改后的目标').goal).toBe('用户修改后的目标');
    expect(withEditedGoal(undefined, world, '无 NCC 的目标').source).toBe('manual');
  });

  it('attaches an abstract style handbook reference without touching other context', () => {
    const context = buildExecutionContextFromPrep(prep);
    const reference = {
      source_title: '参考片段',
      source_rights: 'general_reference' as const,
      handbook: {
        narrative_pacing: { label: '叙事节奏', value: '中速推进。', evidence: null },
        language_density: { label: '语言密度', value: '中等语言密度。', evidence: null },
        dialogue_ratio: { label: '对白比例', value: '对白与叙述交替。', evidence: null },
        scene_progression: { label: '场景推进', value: '用意象带动转场。', evidence: null },
        suspense_structure: { label: '悬念结构', value: '每节保留待解问题。', evidence: null },
        relationship_tension: { label: '人物关系张力', value: '围绕亏欠推进。', evidence: null },
        foreshadowing_pattern: { label: '伏笔埋设/回收方式', value: '先给异常，再延迟解释。', evidence: null },
        do_guidelines: ['保留抽象节奏。'],
        avoid_guidelines: ['不要复用原文句子、人物名、专有设定或标志性桥段。'],
        originality_guidelines: ['正式章节仍需 Studio 审稿。'],
      },
      safety_notes: ['风格手册只是写作参考，不写入 canon。'],
    };

    const withReference = withStyleHandbookReference(context, reference);
    expect(withReference.style_handbook_reference?.source_title).toBe('参考片段');
    // 其余上下文保持不变
    expect(withReference.goal).toBe(context.goal);
    expect(withReference.material_references).toEqual(context.material_references);

    // 传入 null 时清空写作风格参考
    expect(withStyleHandbookReference(withReference, null).style_handbook_reference).toBeNull();
  });
});
