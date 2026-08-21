import type { WorldOverview, ChapterExecutionContext, StoryArcChapter, SerialPlanChapter, WorldCreationMaterialReference } from '../api/types';
import type { ImportBatchWithAssetsResponse, ActiveChapterSessionResponse } from '../api/types';
import type { SerialPlanResponse, StyleHandbookReference } from '../api/types';
import { labelStatus, labelWorldVersion } from './displayLabels';
import { buildManualExecutionContext } from './chapterExecutionContext';


export function describeEvent(event: { event_type: string; payload: Record<string, unknown> }, world: WorldOverview): string {
  const payload = event.payload as Record<string, any>;
  const chapterTitle = payload.chapter_title
    ? `《${payload.chapter_title}》`
    : payload.chapter_id
      ? `第${payload.chapter_id}章`
      : '';

  switch (event.event_type) {
    case 'chapter_approved':
      return `✅ ${chapterTitle} 通过审核，正式纳入故事`;
    case 'character_change': {
      const char = world.current_characters?.find((c) => c.id === payload.object_id);
      const charName = char?.name ?? payload.object_id ?? '某角色';
      const change = payload.change as string;
      if (change === 'created') return `🎭 新角色「${charName}」登场`;
      if (change === 'updated') {
        const after = payload.after as Record<string, any>;
        const before = payload.before as Record<string, any>;
        if (after?.current_goals && before?.current_goals) {
          return `🎭 ${charName} 的目标更新为：${after.current_goals.join('、')}`;
        }
        return `🎭 ${charName} 的状态发生了变化`;
      }
      return `🎭 ${charName} 发生了变化`;
    }
    case 'foreshadow_change': {
      const fs = world.current_foreshadows?.find((f) => f.id === payload.object_id);
      const fsName = fs?.title ?? payload.object_id ?? '某伏笔';
      const change = payload.change as string;
      if (change === 'created') return `🔮 埋下伏笔「${fsName}」`;
      if (change === 'updated') {
        const after = payload.after as Record<string, any>;
        if (after?.status) {
          return `🔮 伏笔「${fsName}」${labelStatus(after.status)}`;
        }
        return `🔮 伏笔「${fsName}」发生了变化`;
      }
      return `🔮 伏笔「${fsName}」发生了变化`;
    }
    case 'world_version_increment':
      return `📖 世界进度更新至${labelWorldVersion(payload.world_version_after ?? event.event_type)}`;
    default:
      return `${event.event_type}`;
  }
}

export function isOpenForeshadow(status: string): boolean {
  return !['fully_resolved', 'resolved', 'abandoned'].includes(status);
}

export function openForeshadows(world: WorldOverview): WorldOverview['foreshadows'] {
  return world.foreshadows
    .filter((item) => isOpenForeshadow(item.status))
    .sort((a, b) => (b.urgency_level ?? 0) - (a.urgency_level ?? 0));
}

export function buildFirstChapterQuickStartGoal(world: WorldOverview): string {
  const characterWithGoal = world.characters.find((character) =>
    Boolean(character.name.trim() && character.current_goals?.[0]?.trim()),
  );
  if (characterWithGoal) {
    return `建议让${characterWithGoal.name}先尝试${characterWithGoal.current_goals[0].trim()}，并在行动中建立第一章冲突。`;
  }

  const urgentForeshadow = openForeshadows(world)[0];
  if (urgentForeshadow) {
    return `建议围绕伏笔「${urgentForeshadow.title}」安排一次会迫使角色行动的开场事件。`;
  }

  const canonExcerpt = world.truth_canon.trim().slice(0, 72) || '尚待展开的世界设定';
  return `建议从「${world.title}」的一个具体场景开篇，让角色面对世界设定中的异常：${canonExcerpt}${world.truth_canon.trim().length > canonExcerpt.length ? '…' : ''}`;
}

export function materialReferencesFromImportBatches(batches: ImportBatchWithAssetsResponse[]): WorldCreationMaterialReference[] {
  return batches.flatMap((batch) => batch.assets.map((asset) => ({
    source: 'import_node' as const,
    asset_id: asset.id,
    title: asset.title,
    summary: asset.summary,
    asset_pool: asset.asset_pool,
    source_rights: 'general_reference' as const,
  })));
}

export function worldLoadFailureMessage(error: unknown): string {
  if (error instanceof Error && error.message === 'MULTIPLE_ACTIVE_CHAPTERS') {
    return '检测到多个未完成章节，已停止自动恢复和新建章节。请先由管理员核对并保留正确的 Studio 草稿。';
  }
  return error instanceof Error ? error.message : '加载世界失败';
}

export function dashboardActions(world: WorldOverview, isArchivedWorld: boolean, hasActiveChapter: boolean): Array<{ label: string; detail: string; primary?: boolean }> {
  const urgentForeshadow = openForeshadows(world)[0];
  const needsFirstChapterOnboarding = !isArchivedWorld && world.approved_chapter_count === 0 && world.story_arc.length === 0;
  const actions = [
    isArchivedWorld
      ? { label: '恢复写作后继续下一章', detail: '这本小说已归档；恢复写作后再继续推进正史。' }
      : hasActiveChapter
        ? { label: '继续进行中的章节', detail: '恢复已保留的 Studio 创作进度，不会创建第二个未批准章节。', primary: true }
        : needsFirstChapterOnboarding
          ? { label: '直接写第一章或生成故事大纲', detail: '这本小说还没有写入正史；可直接生成第一章草稿，也可先补充故事大纲。' }
          : { label: '继续下一章', detail: `下一章会继承世界进度${labelWorldVersion(world.world_version)}和已写入正史的变化。`, primary: true },
  ];
  if (urgentForeshadow) {
    actions.push({
      label: '回收或推进悬念/伏笔',
      detail: `优先处理「${urgentForeshadow.title}」，紧迫度 ${urgentForeshadow.urgency_level ?? 0}。`,
    });
  } else {
    actions.push({ label: '埋设新的悬念/伏笔', detail: '当前没有待处理悬念/伏笔，可以为下一章准备新的牵引线。' });
  }
  actions.push(
    world.recent_events.length > 0
      ? { label: '检查世界历史记录', detail: `最近有 ${world.recent_events.length} 条世界历史记录，可确认正史连续性。` }
      : { label: '写入第一条世界历史记录', detail: '批准第一章后，这里会出现世界历史记录证据。' },
  );
  return actions;
}

export function WorldOperationsDashboard({ world, isArchivedWorld, hasActiveChapter, onContinue, onShowForeshadows, onShowArchive }: { world: WorldOverview; isArchivedWorld: boolean; hasActiveChapter: boolean; onContinue: () => void; onShowForeshadows: () => void; onShowArchive: () => void }) {
  const activeCharacters = world.characters.slice(0, 3);
  const urgentForeshadows = openForeshadows(world).slice(0, 3);
  const actions = dashboardActions(world, isArchivedWorld, hasActiveChapter);

  return (
    <section className="workbench-panel space-y-6" aria-label="今日创作看板">
      <div>
        <p className="chapter-kicker">今日创作</p>
        <h2 className="text-2xl font-black text-[#34210f]">今日创作看板</h2>
        <p className="manuscript mt-2 text-sm text-[#5e3b1c]">今天这个故事世界需要处理什么？先看正史进度、活跃角色、悬念/伏笔和世界历史记录。</p>
      </div>
      <div className="workbench-metric-strip text-sm">
        <p className="rounded-2xl bg-white/65 p-4 font-black text-[#3b2511]">世界进度：{labelWorldVersion(world.world_version)}</p>
        <p className="rounded-2xl bg-white/65 p-4 font-black text-[#3b2511]">已写入正史章节：{world.approved_chapter_count}</p>
        <p className="rounded-2xl bg-white/65 p-4 font-black text-[#3b2511]">近期世界历史记录：{world.recent_events.length}</p>
        <p className="rounded-2xl bg-white/65 p-4 font-black text-[#3b2511]">待处理悬念/伏笔：{openForeshadows(world).length}</p>
      </div>
      <section>
        <h3 className="font-black text-[#3b2511]">今天建议处理什么</h3>
        <div className="workbench-action-list mt-4 gap-4" data-testid="world-dashboard-actions">
          {actions.map((action) => (
            <article key={action.label} className="rounded-2xl bg-white/60 p-4">
              {action.primary && !isArchivedWorld ? (
                <button className="primary-button" type="button" onClick={onContinue}>{action.label}</button>
              ) : (
                <p className="font-black text-[#3b2511]">{action.label}</p>
              )}
              <p className="manuscript mt-2 text-sm">{action.detail}</p>
            </article>
          ))}
        </div>
      </section>
      <div className="workbench-side-list gap-5" data-testid="world-dashboard-sidebars">
        <section className="rounded-2xl bg-white/55 p-4">
          <h3 className="font-black text-[#3b2511]">活跃角色</h3>
          <div className="mt-3 space-y-2">
            {activeCharacters.length === 0 && <p className="ink-muted text-sm">暂无活跃角色。</p>}
            {activeCharacters.map((character) => (
              <p className="manuscript text-sm" key={character.id}>{character.name}：{character.current_goals.join('、') || character.status}</p>
            ))}
          </div>
        </section>
        <section className="rounded-2xl bg-white/55 p-4">
          <h3 className="font-black text-[#3b2511]">紧迫悬念/伏笔</h3>
          <div className="mt-3 space-y-2">
            {urgentForeshadows.length === 0 && <p className="ink-muted text-sm">暂无待处理悬念/伏笔。</p>}
            {urgentForeshadows.map((item) => (
              <p className="manuscript text-sm" key={item.id}>{item.title}：{labelStatus(item.status)} · 紧迫度 {item.urgency_level ?? 0}</p>
            ))}
          </div>
          <button className="secondary-button mt-3" type="button" onClick={onShowForeshadows}>查看悬念/伏笔账本</button>
        </section>
        <section className="rounded-2xl bg-white/55 p-4">
          <h3 className="font-black text-[#3b2511]">近期世界历史记录</h3>
          <div className="mt-3 space-y-2">
            {world.recent_events.length === 0 && <p className="ink-muted text-sm">还没有正式写入的章节事件。</p>}
            {world.recent_events.slice(0, 3).map((event) => (
              <p className="manuscript text-sm" key={event.id}>{describeEvent(event, world)}</p>
            ))}
          </div>
          <button className="secondary-button mt-3" type="button" onClick={onShowArchive}>查看章节历史</button>
        </section>
      </div>
    </section>
  );
}

export function StoryArcCard({ chapter, expanded, onToggle }: { chapter: StoryArcChapter; expanded: boolean; onToggle: () => void }) {
  const detailId = `story-arc-chapter-${chapter.chapter_number}-detail`;
  const buttonLabel = `第 ${chapter.chapter_number} 章 · ${chapter.title}${chapter.foreshadow_hints.length ? ` · ${chapter.foreshadow_hints.length} 条伏笔` : ''}`;

  return (
    <article className="rounded-2xl border border-amber-900/15 bg-white/35 p-2">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 rounded-xl px-3 py-2 text-left transition-colors hover:bg-amber-50/70"
        aria-expanded={expanded}
        aria-controls={detailId}
        aria-label={buttonLabel}
        onClick={onToggle}
      >
        <span className="min-w-0 flex-1 truncate text-sm font-black text-[#34210f]">
          第 {chapter.chapter_number} 章 · {chapter.title}
        </span>
        <span className="flex shrink-0 items-center gap-2 text-xs font-bold text-[#5e3b1c]">
          {chapter.foreshadow_hints.length > 0 && (
            <span className="rounded-full border border-amber-900/15 bg-amber-100/70 px-2 py-0.5">{chapter.foreshadow_hints.length} 条伏笔</span>
          )}
          <span aria-hidden="true">{expanded ? '收起' : '展开'}</span>
        </span>
      </button>
      {expanded && (
        <div id={detailId} className="mt-3 grid gap-3 px-2 pb-2 md:grid-cols-2">
          <div className="rounded-2xl bg-amber-50/60 p-3 md:col-span-2">
            <p className="text-sm font-bold text-[#5e3b1c]">章节摘要</p>
            <p className="manuscript mt-1">{chapter.summary}</p>
          </div>
          <div className="rounded-2xl bg-amber-50/60 p-3">
            <p className="text-sm font-bold text-[#5e3b1c]">核心冲突</p>
            <p className="manuscript mt-1">{chapter.core_conflict}</p>
          </div>
          <div className="rounded-2xl bg-amber-50/60 p-3">
            <p className="text-sm font-bold text-[#5e3b1c]">POV 建议</p>
            <p className="manuscript mt-1">{chapter.pov_suggestion}</p>
          </div>
          <div className="rounded-2xl bg-amber-50/60 p-3 md:col-span-2">
            <p className="text-sm font-bold text-[#5e3b1c]">伏笔提示</p>
            <p className="manuscript mt-1">{chapter.foreshadow_hints.length ? chapter.foreshadow_hints.join('、') : '无指定伏笔'}</p>
          </div>
        </div>
      )}
    </article>
  );
}

export function buildStoryArcGoal(chapter: StoryArcChapter) {
  return `${chapter.title}：${chapter.summary}`;
}

export function buildStoryArcExecutionContext(world: WorldOverview, chapter: StoryArcChapter): ChapterExecutionContext {
  return {
    source: 'manual',
    source_world_version: world.world_version,
    next_chapter_number: chapter.chapter_number,
    goal: buildStoryArcGoal(chapter),
    recommended_pov: { character_id: null, name: chapter.pov_suggestion || null },
    source_signals: ['story_arc_planner'],
    priority_characters: [],
    priority_foreshadows: [],
    progression_hints: [],
    continuity_warnings: [],
    recent_events: [],
    material_references: [],
  };
}

export function buildWorldCreationDraftExecutionContext(world: WorldOverview, firstChapterGoal: string): ChapterExecutionContext {
  return {
    source: 'manual',
    source_world_version: world.world_version,
    next_chapter_number: 1,
    goal: firstChapterGoal,
    recommended_pov: { character_id: null, name: null },
    source_signals: ['world_creation_draft'],
    priority_characters: [],
    priority_foreshadows: [],
    progression_hints: [],
    continuity_warnings: [],
    recent_events: [],
    material_references: [],
  };
}

export function buildSerialPlanExecutionContext(
  world: WorldOverview,
  chapter: SerialPlanChapter,
  convergenceGuidance: SerialPlanResponse['convergence_guidance'],
  reviewGuardrails: string[],
): ChapterExecutionContext {
  const context = buildManualExecutionContext(world, chapter.goal);
  const priorityForeshadowIds = convergenceGuidance.priority_foreshadows.map((item) => item.foreshadow_id);
  const reviewGuardrailWarnings = reviewGuardrails.map((message) => ({
    severity: 'info',
    category: 'serial_plan_review_boundary',
    message,
    related_character_ids: [],
    related_foreshadow_ids: [],
  }));
  const progressionHints = [
    ...(chapter.foreshadow_hints.length
      ? [
          {
            hint_type: 'foreshadow' as const,
            priority: 'medium' as const,
            title: '连载队列伏笔提示',
            rationale: `该目标来自故事弧线，提示关联悬念/伏笔：${chapter.foreshadow_hints.join('、')}。`,
            suggested_next_beat: '在 Studio 草稿中推进或回应这些既有悬念/伏笔；是否写入正史仍由用户审核决定。',
            related_character_ids: [],
            related_foreshadow_ids: [],
            can_seed_next_chapter_goal: false,
          },
        ]
      : []),
    {
      hint_type: 'plot' as const,
      priority: convergenceGuidance.mode === 'balanced' || convergenceGuidance.mode === 'expand' ? 'medium' as const : 'high' as const,
      title: '自动连载叙事收束提示',
      rationale: `${convergenceGuidance.mode_label}：${convergenceGuidance.recommendation}`,
      suggested_next_beat: '把收束提示作为 Studio 写作参考；是否推进、回收或关闭伏笔仍由用户审稿后决定。',
      related_character_ids: [],
      related_foreshadow_ids: priorityForeshadowIds,
      can_seed_next_chapter_goal: false,
    },
  ];
  return {
    ...context,
    next_chapter_number: chapter.chapter_number,
    recommended_pov: { character_id: null, name: chapter.pov_suggestion || null },
    source_signals: ['serial_plan_preview', chapter.source, 'serial_plan_convergence_guidance'],
    priority_foreshadows: convergenceGuidance.priority_foreshadows.map((item) => ({
      foreshadow_id: item.foreshadow_id,
      title: item.title,
      status: item.status,
      urgency_level: item.urgency_level,
      reason: item.pressure_reasons.join('、') || item.pressure_level,
    })),
    progression_hints: progressionHints,
    continuity_warnings: reviewGuardrailWarnings,
  };
}

export type FirstChapterLaunchpadProps = {
  world: WorldOverview;
  nextChapter: StoryArcChapter | null;
  arcLoading: boolean;
  onGenerateArc: () => void;
  onLaunchChapter: (chapter: StoryArcChapter) => void;
  onQuickStart: () => void;
  quickStartGoal: string;
};

export function FirstChapterLaunchpad({ world, nextChapter, arcLoading, onGenerateArc, onLaunchChapter, onQuickStart, quickStartGoal }: FirstChapterLaunchpadProps) {
  return (
    <article className="mt-8 rounded-2xl border border-amber-900/15 bg-amber-100/60 p-4 shadow-sm">
      <p className="chapter-kicker">第一章起点</p>
      {world.story_arc.length === 0 ? (
        <div className="mt-3">
          <p className="manuscript text-sm text-[#5e3b1c]">不必先规划 10 章；可以直接写第一章，也可先生成故事大纲。</p>
          <p className="manuscript mt-2 text-sm">建议首章目标：{quickStartGoal}</p>
          <p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">只生成草稿，确认前不写入正史。</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button className="primary-button" type="button" onClick={onQuickStart}>生成第一章草稿并进入 Studio</button>
            <button className="secondary-button" type="button" disabled={arcLoading} onClick={onGenerateArc}>
              {arcLoading ? '故事弧线规划中…' : '生成第一轮故事弧线'}
            </button>
          </div>
        </div>
      ) : nextChapter ? (
        <div className="mt-3 space-y-3">
          <p className="text-sm font-black text-[#5e3b1c]">下一章 · 第 {nextChapter.chapter_number} 章</p>
          <h2 className="text-2xl font-black text-[#34210f]">{nextChapter.title}</h2>
          <p className="manuscript text-sm">{nextChapter.summary}</p>
          <div className="grid gap-2 text-sm md:grid-cols-2">
            <p className="rounded-xl bg-white/45 p-3"><span className="font-bold text-[#5e3b1c]">POV：</span>{nextChapter.pov_suggestion}</p>
            <p className="rounded-xl bg-white/45 p-3"><span className="font-bold text-[#5e3b1c]">冲突：</span>{nextChapter.core_conflict}</p>
          </div>
          <button className="primary-button" type="button" onClick={() => onLaunchChapter(nextChapter)}>用此目标进入创作台</button>
        </div>
      ) : (
        <div className="mt-3">
          <p className="manuscript text-sm text-[#5e3b1c]">当前故事弧线已写完。可重新生成故事大纲，或在叙事运营台继续准备下一章。</p>
          <button className="secondary-button mt-4" type="button" disabled={arcLoading} onClick={onGenerateArc}>
            {arcLoading ? '故事弧线规划中…' : '重新生成故事大纲'}
          </button>
        </div>
      )}
    </article>
  );
}

export type SerialPlanPanelProps = {
  serialPlan: SerialPlanResponse | null;
  loading: boolean;
  error: string;
  onGenerate: () => void;
  onLaunchChapter: (chapter: SerialPlanChapter) => void;
};

export function SerialPlanPanel({ serialPlan, loading, error, onGenerate, onLaunchChapter }: SerialPlanPanelProps) {
  return (
    <section className="book-card p-5" aria-label="自动连载试验">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="chapter-kicker">自动连载试验</p>
          <h2 className="mt-2 text-2xl font-black text-[#34210f]">后续章节目标队列</h2>
          <p className="manuscript mt-2 text-sm text-[#5e3b1c]">生成后续章节目标队列；不会自动写正文、不会写入正史或推进世界进度。每章仍需进入 Studio 审稿。</p>
        </div>
        <button className="primary-button" type="button" disabled={loading} onClick={onGenerate}>
          {loading ? '连载队列生成中…' : '生成连载队列'}
        </button>
      </div>
      {error && <p className="paper-error mt-4" role="alert">{error}</p>}
      {serialPlan && (
        <div className="mt-5 space-y-4">
          <p className="ink-muted text-sm">已批准章节：{serialPlan.approved_chapter_count} · 来源世界版本：第 {serialPlan.world_version} 版</p>
          <ul className="space-y-1 text-sm font-bold text-[#5e3b1c]">
            {serialPlan.safety_notes.map((note) => <li key={note}>{note}</li>)}
          </ul>
          <aside className="rounded-2xl border border-amber-900/15 bg-white/50 p-4" aria-label="连载队列审稿边界">
            <p className="text-sm font-black text-[#5e3b1c]">逐章审稿边界</p>
            <ul className="mt-2 space-y-1 text-sm font-bold text-[#5e3b1c]">
              {serialPlan.review_guardrails.map((note) => <li key={note}>{note}</li>)}
            </ul>
          </aside>
          <article className="rounded-2xl bg-amber-50/70 p-4" aria-label="叙事收束提示">
            <p className="chapter-kicker">叙事收束提示</p>
            <h3 className="mt-2 text-lg font-black text-[#34210f]">{serialPlan.convergence_guidance.mode_label}</h3>
            <p className="manuscript mt-2 text-sm">{serialPlan.convergence_guidance.recommendation}</p>
            <div className="mt-3 grid gap-2 text-sm md:grid-cols-4">
              <p className="rounded-xl bg-white/50 p-3 font-bold text-[#5e3b1c]">开放伏笔：{serialPlan.convergence_guidance.open_foreshadow_count}</p>
              <p className="rounded-xl bg-white/50 p-3 font-bold text-[#5e3b1c]">高压伏笔：{serialPlan.convergence_guidance.high_pressure_count}</p>
              <p className="rounded-xl bg-white/50 p-3 font-bold text-[#5e3b1c]">久未推进：{serialPlan.convergence_guidance.stale_count}</p>
              <p className="rounded-xl bg-white/50 p-3 font-bold text-[#5e3b1c]">逾期伏笔：{serialPlan.convergence_guidance.overdue_count}</p>
            </div>
            {serialPlan.convergence_guidance.priority_foreshadows.length > 0 && (
              <div className="mt-3 space-y-2 text-sm">
                <p className="font-black text-[#5e3b1c]">优先处理</p>
                {serialPlan.convergence_guidance.priority_foreshadows.map((item) => (
                  <p key={item.foreshadow_id} className="manuscript rounded-xl bg-white/45 p-3">
                    {item.title} · 紧迫度 {item.urgency_level} · {item.pressure_reasons.join('、') || item.pressure_level}
                  </p>
                ))}
              </div>
            )}
            <ul className="mt-3 space-y-1 text-xs font-bold text-[#5e3b1c]">
              {serialPlan.convergence_guidance.guidance_notes.map((note) => <li key={note}>{note}</li>)}
            </ul>
          </article>
          {serialPlan.queue.length === 0 ? (
            <p className="manuscript rounded-2xl bg-amber-50/60 p-3 text-sm">没有可用的后续章节目标。先生成故事弧线或批准下一章后再刷新队列。</p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {serialPlan.queue.map((chapter) => (
                <article key={`${chapter.source}-${chapter.chapter_number}`} className="rounded-2xl border border-amber-900/15 bg-white/40 p-4">
                  <p className="text-sm font-black text-[#5e3b1c]">队列第 {chapter.chapter_number} 章</p>
                  <h3 className="mt-1 text-xl font-black text-[#34210f]">{chapter.title}</h3>
                  <p className="manuscript mt-2 text-sm">{chapter.goal}</p>
                  <div className="mt-3 space-y-2 text-sm">
                    <p><span className="font-bold text-[#5e3b1c]">冲突：</span>{chapter.core_conflict || '未指定'}</p>
                    <p><span className="font-bold text-[#5e3b1c]">POV：</span>{chapter.pov_suggestion || '未指定'}</p>
                    <p><span className="font-bold text-[#5e3b1c]">伏笔：</span>{chapter.foreshadow_hints.length ? chapter.foreshadow_hints.join('、') : '无指定伏笔'}</p>
                  </div>
                  <button className="secondary-button mt-4" type="button" onClick={() => onLaunchChapter(chapter)}>用此目标进入 Studio</button>
                </article>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export type ArchivedWorldPauseCardProps = {
  archiveLoading: boolean;
  onReturnToBookshelf: () => void;
  onRestoreWriting: () => void;
};

export function ArchivedWorldPauseCard({ archiveLoading, onReturnToBookshelf, onRestoreWriting }: ArchivedWorldPauseCardProps) {
  return (
    <article className="mt-8 rounded-2xl border border-amber-900/15 bg-amber-100/70 p-4 shadow-sm">
      <p className="chapter-kicker">已归档小说</p>
      <h2 className="mt-2 text-2xl font-black text-[#34210f]">已归档：写作已暂停</h2>
      <p className="manuscript mt-2 text-sm text-[#5e3b1c]">这本小说已从活跃创作中移出。快照、章节、伏笔和导出都还在。恢复写作后再进入创作台。</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="secondary-button" type="button" onClick={onReturnToBookshelf}>返回作品书架</button>
        <button className="primary-button" type="button" disabled={archiveLoading} onClick={onRestoreWriting}>
          {archiveLoading ? '恢复中...' : '恢复写作'}
        </button>
      </div>
    </article>
  );
}

export type FirstChapterOnboardingCardProps = {
  arcLoading: boolean;
  quickStartGoal: string;
  onQuickStart: () => void;
  onGenerateArc: () => Promise<void> | void;
  onOpenWriteTab: () => void;
};

export function FirstChapterOnboardingCard({ arcLoading, quickStartGoal, onQuickStart, onGenerateArc, onOpenWriteTab }: FirstChapterOnboardingCardProps) {
  return (
    <article className="mt-6 rounded-3xl border-2 border-amber-900/20 bg-amber-100/80 p-5 shadow-sm" aria-label="第一章写作引导">
      <p className="chapter-kicker">第一步</p>
      <h2 className="mt-2 text-2xl font-black text-[#34210f]">直接写第一章，或先生成故事大纲</h2>
      <p className="manuscript mt-2 text-sm text-[#5e3b1c]">这本小说还没有写入正史。故事大纲是可选增强，不必先规划 10 章。</p>
      <p className="manuscript mt-2 text-sm">建议首章目标：{quickStartGoal}</p>
      <p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">只生成草稿，确认前不写入正史。</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="primary-button" type="button" onClick={onQuickStart}>生成第一章草稿并进入 Studio</button>
        <button className="secondary-button" type="button" disabled={arcLoading} onClick={() => void onGenerateArc()}>
          {arcLoading ? '故事弧线规划中…' : '生成故事大纲'}
        </button>
        <button className="secondary-button" type="button" onClick={onOpenWriteTab}>查看继续创作页</button>
      </div>
    </article>
  );
}
