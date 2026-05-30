import type { ChapterExecutionContext, NextChapterPrepResponse, WorldOverview } from '../api/types';

export function buildExecutionContextFromPrep(prep: NextChapterPrepResponse): ChapterExecutionContext {
  return {
    source: 'next_chapter_prep',
    source_world_version: prep.world_version,
    next_chapter_number: prep.next_chapter_number,
    goal: prep.suggested_goal,
    recommended_pov: {
      character_id: prep.recommended_pov_character_id,
      name: prep.recommended_pov_character_name,
    },
    source_signals: prep.source_signals,
    priority_characters: prep.priority_characters,
    priority_foreshadows: prep.priority_foreshadows,
    progression_hints: prep.progression_hints,
    continuity_warnings: prep.continuity_warnings,
    recent_events: prep.recent_events.map(({ id, event_type, world_version_before, world_version_after, created_at }) => ({
      id,
      event_type,
      world_version_before,
      world_version_after,
      created_at,
    })),
  };
}

export function buildManualExecutionContext(world: WorldOverview, goal: string): ChapterExecutionContext {
  return {
    source: 'manual',
    source_world_version: world.world_version,
    next_chapter_number: world.approved_chapter_count + 1,
    goal,
    recommended_pov: { character_id: null, name: null },
    source_signals: ['manual'],
    priority_characters: [],
    priority_foreshadows: [],
    progression_hints: [],
    continuity_warnings: [],
    recent_events: [],
  };
}

export function withEditedGoal(
  context: ChapterExecutionContext | undefined,
  world: WorldOverview,
  goal: string,
): ChapterExecutionContext {
  if (context) return { ...context, goal };
  return buildManualExecutionContext(world, goal);
}
