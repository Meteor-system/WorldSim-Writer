import { useEffect, useRef, useState } from 'react';
import {
  apiRequest,
  assignWorldTag,
  bulkAssignWorldTag,
  compareWorldSnapshots,
  createSampleWorld,
  createWorld,
  createWorldFromSeed,
  createWorldSnapshot,
  createWorldTag,
  deleteWorldTag,
  exportWorldArchiveMarkdown,
  generateStoryArc,
  getArcPlan,
  getChapterHistory,
  getChapterHistoryDetail,
  getNarrativeHealth,
  getNextChapterPrep,
  getOpenThreads,
  getWorldEvents,
  getWorldPulse,
  getWorldSeed,
  getWorldTag,
  listWorldSeeds,
  listWorldSnapshots,
  listWorldTags,
  mergeWorldTag,
  searchWorld,
  unassignWorldTag,
  updateWorldStatus,
  updateWorldTag,
} from '../api/client';
import type { ArcPlanResponse, ChapterExecutionContext, ChapterHistoryResponse, NarrativeHealthResponse, NextChapterPrepResponse, OpenThreadsResponse, StoryArcChapter, StudioLaunchContext, WorldCreateRequest, WorldOverview, WorldPulseResponse, WorldSeedSummary, WorldSummary } from '../api/types';
import { CharacterManager } from '../components/CharacterManager';
import { ForeshadowManager } from '../components/ForeshadowManager';
import { RelationManager } from '../components/RelationManager';
import { ArcPlanPanel } from './ArcPlanPanel';
import { ChapterHistoryPanel } from './ChapterHistoryPanel';
import { NarrativeHealthPanel } from './NarrativeHealthPanel';
import { NextChapterPrepPanel } from './NextChapterPrepPanel';
import { OpenThreadsPanel } from './OpenThreadsPanel';
import { WorldArchivePanel } from './WorldArchivePanel';
import { WorldCreationForm } from './WorldCreationForm';
import { WorldPulsePanel } from './WorldPulsePanel';
import { WorldSearchPanel } from './WorldSearchPanel';
import { WorldTagsPanel } from './WorldTagsPanel';
import { WorldTimelinePanel } from './WorldTimelinePanel';

type Props = { onEnterStudio: (world: WorldOverview, context?: StudioLaunchContext) => void; autoFocusTitle?: boolean };

type Tab = 'overview' | 'characters' | 'relations' | 'foreshadows';

const TABS: { key: Tab; label: string }[] = [
  { key: 'overview', label: '世界概览' },
  { key: 'characters', label: '角色管理' },
  { key: 'relations', label: '关系管理' },
  { key: 'foreshadows', label: '伏笔账本' },
];

function describeEvent(event: { event_type: string; payload: Record<string, unknown> }, world: WorldOverview): string {
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
          const statusMap: Record<string, string> = {
            planted: '已埋下', advanced: '推进中', partially_resolved: '部分揭晓',
            fully_resolved: '已揭晓', abandoned: '已废弃',
          };
          return `🔮 伏笔「${fsName}」${statusMap[after.status] ?? after.status}`;
        }
        return `🔮 伏笔「${fsName}」发生了变化`;
      }
      return `🔮 伏笔「${fsName}」发生了变化`;
    }
    case 'world_version_increment':
      return `📖 世界版本更新至 v${payload.world_version_after ?? event.event_type}`;
    default:
      return `${event.event_type}`;
  }
}

function StoryArcCard({ chapter, expanded, onToggle }: { chapter: StoryArcChapter; expanded: boolean; onToggle: () => void }) {
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

function buildStoryArcGoal(chapter: StoryArcChapter) {
  return `${chapter.title}：${chapter.summary}`;
}

function buildStoryArcExecutionContext(world: WorldOverview, chapter: StoryArcChapter): ChapterExecutionContext {
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
  };
}

type FirstChapterLaunchpadProps = {
  world: WorldOverview;
  nextChapter: StoryArcChapter | null;
  arcLoading: boolean;
  onGenerateArc: () => void;
  onLaunchChapter: (chapter: StoryArcChapter) => void;
};

function FirstChapterLaunchpad({ world, nextChapter, arcLoading, onGenerateArc, onLaunchChapter }: FirstChapterLaunchpadProps) {
  return (
    <article className="mt-8 rounded-2xl border border-amber-900/15 bg-amber-100/60 p-4 shadow-sm">
      <p className="chapter-kicker">First Chapter Launchpad</p>
      {world.story_arc.length === 0 ? (
        <div className="mt-3">
          <p className="manuscript text-sm text-[#5e3b1c]">先生成前 10 章故事弧线，再把下一章目标带入创作台。</p>
          <button className="primary-button mt-4" type="button" disabled={arcLoading} onClick={onGenerateArc}>
            {arcLoading ? '规划中...' : '生成第一轮故事弧线'}
          </button>
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
          <p className="manuscript text-sm text-[#5e3b1c]">当前故事弧线已写完。可重新生成故事大纲，或在 Narrative Control Center 继续准备下一章。</p>
          <button className="secondary-button mt-4" type="button" disabled={arcLoading} onClick={onGenerateArc}>
            {arcLoading ? '规划中...' : '重新生成故事大纲'}
          </button>
        </div>
      )}
    </article>
  );
}

type ArchivedWorldPauseCardProps = {
  archiveLoading: boolean;
  onReturnToBookshelf: () => void;
  onRestoreWriting: () => void;
};

function ArchivedWorldPauseCard({ archiveLoading, onReturnToBookshelf, onRestoreWriting }: ArchivedWorldPauseCardProps) {
  return (
    <article className="mt-8 rounded-2xl border border-amber-900/15 bg-amber-100/70 p-4 shadow-sm">
      <p className="chapter-kicker">Archived Novel</p>
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

export function WorldPage({ onEnterStudio, autoFocusTitle = true }: Props) {
  const [world, setWorld] = useState<WorldOverview | null>(null);
  const [worlds, setWorlds] = useState<WorldSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showCreationForm, setShowCreationForm] = useState(false);
  const [error, setError] = useState('');
  const [archiveLoading, setArchiveLoading] = useState(false);
  const [archiveError, setArchiveError] = useState('');
  const [seedLibrary, setSeedLibrary] = useState<WorldSeedSummary[]>([]);
  const [seedLibraryLoading, setSeedLibraryLoading] = useState(false);
  const [seedLibraryError, setSeedLibraryError] = useState('');
  const [arcLoading, setArcLoading] = useState(false);
  const [chapterHistory, setChapterHistory] = useState<ChapterHistoryResponse | null>(null);
  const [chapterHistoryLoading, setChapterHistoryLoading] = useState(false);
  const [chapterHistoryError, setChapterHistoryError] = useState('');
  const [nextPrep, setNextPrep] = useState<NextChapterPrepResponse | null>(null);
  const [nextPrepLoading, setNextPrepLoading] = useState(false);
  const [nextPrepError, setNextPrepError] = useState('');
  const [narrativeHealth, setNarrativeHealth] = useState<NarrativeHealthResponse | null>(null);
  const [narrativeHealthLoading, setNarrativeHealthLoading] = useState(false);
  const [narrativeHealthError, setNarrativeHealthError] = useState('');
  const [openThreads, setOpenThreads] = useState<OpenThreadsResponse | null>(null);
  const [openThreadsLoading, setOpenThreadsLoading] = useState(false);
  const [openThreadsError, setOpenThreadsError] = useState('');
  const [worldPulse, setWorldPulse] = useState<WorldPulseResponse | null>(null);
  const [worldPulseLoading, setWorldPulseLoading] = useState(false);
  const [worldPulseError, setWorldPulseError] = useState('');
  const [arcPlan, setArcPlan] = useState<ArcPlanResponse | null>(null);
  const [arcPlanLoading, setArcPlanLoading] = useState(false);
  const [arcPlanError, setArcPlanError] = useState('');
  const [selectedExecutionContext, setSelectedExecutionContext] = useState<ChapterExecutionContext | null>(null);
  const [expandedStoryArcChapters, setExpandedStoryArcChapters] = useState<number[]>([]);
  const [tab, setTab] = useState<Tab>('overview');
  const titleRef = useRef<HTMLHeadingElement>(null);

  async function loadNarrativeControlCenter(worldId: number) {
    setChapterHistoryLoading(true);
    setNextPrepLoading(true);
    setNarrativeHealthLoading(true);
    setOpenThreadsLoading(true);
    setWorldPulseLoading(true);
    setArcPlanLoading(true);
    setChapterHistoryError('');
    setNextPrepError('');
    setNarrativeHealthError('');
    setOpenThreadsError('');
    setWorldPulseError('');
    setArcPlanError('');
    try {
      setChapterHistory(await getChapterHistory(worldId));
    } catch {
      setChapterHistory(null);
      setChapterHistoryError('章节历史暂不可用');
    } finally {
      setChapterHistoryLoading(false);
    }
    try {
      setNextPrep(await getNextChapterPrep(worldId));
    } catch {
      setNextPrep(null);
      setNextPrepError('下一章准备台暂不可用');
    } finally {
      setNextPrepLoading(false);
    }
    try {
      setNarrativeHealth(await getNarrativeHealth(worldId));
    } catch {
      setNarrativeHealth(null);
      setNarrativeHealthError('叙事健康度暂不可用');
    } finally {
      setNarrativeHealthLoading(false);
    }
    try {
      setOpenThreads(await getOpenThreads(worldId));
    } catch {
      setOpenThreads(null);
      setOpenThreadsError('开放线索看板暂不可用');
    } finally {
      setOpenThreadsLoading(false);
    }
    try {
      setWorldPulse(await getWorldPulse(worldId));
    } catch {
      setWorldPulse(null);
      setWorldPulseError('世界心跳暂不可用');
    } finally {
      setWorldPulseLoading(false);
    }
    try {
      setArcPlan(await getArcPlan(worldId));
    } catch {
      setArcPlan(null);
      setArcPlanError('篇章模式暂不可用');
    } finally {
      setArcPlanLoading(false);
    }
  }

  async function loadSeedLibrary() {
    setSeedLibraryLoading(true);
    setSeedLibraryError('');
    try {
      const response = await listWorldSeeds();
      setSeedLibrary(response.seeds);
    } catch {
      setSeedLibrary([]);
      setSeedLibraryError('世界胚胎库暂不可用');
    } finally {
      setSeedLibraryLoading(false);
    }
  }

  async function openWorld(worldId: number) {
    setError('');
    setArchiveError('');
    const overview = await apiRequest<WorldOverview>(`/worlds/${worldId}/overview`);
    setWorld(overview);
    setWorlds((current) => [...current.filter((item) => item.id !== overview.id), overview]);
    setShowCreationForm(false);
    setSelectedExecutionContext(null);
    setTab('overview');
    void loadNarrativeControlCenter(overview.id);
  }

  async function loadWorld() {
    setError('');
    try {
      const loadedWorlds = await apiRequest<WorldSummary[]>('/worlds');
      setWorlds(loadedWorlds);
      if (loadedWorlds.length === 0) {
        setWorld(null);
        setShowCreationForm(true);
        void loadSeedLibrary();
      } else if (loadedWorlds.length === 1 && loadedWorlds[0].status !== 'archived') {
        await openWorld(loadedWorlds[0].id);
      } else {
        setWorld(null);
        setShowCreationForm(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载世界失败');
    } finally {
      setLoading(false);
    }
  }

  async function submitWorld(payload: WorldCreateRequest) {
    setCreating(true);
    setError('');
    try {
      const created = await createWorld(payload);
      const overview = await apiRequest<WorldOverview>(`/worlds/${created.id}/overview`);
      setWorld(overview);
      setWorlds((current) => [...current.filter((item) => item.id !== overview.id), overview]);
      setShowCreationForm(false);
      void loadNarrativeControlCenter(overview.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建世界失败');
    } finally {
      setCreating(false);
    }
  }

  async function submitSampleWorld() {
    setCreating(true);
    setError('');
    try {
      const created = await createSampleWorld();
      const overview = await apiRequest<WorldOverview>(`/worlds/${created.id}/overview`);
      setWorld(overview);
      setWorlds((current) => [...current.filter((item) => item.id !== overview.id), overview]);
      setShowCreationForm(false);
      void loadNarrativeControlCenter(overview.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建世界失败');
    } finally {
      setCreating(false);
    }
  }

  async function submitSeedWorld(seedKey: string) {
    setCreating(true);
    setError('');
    try {
      const created = await createWorldFromSeed(seedKey);
      const overview = await apiRequest<WorldOverview>(`/worlds/${created.id}/overview`);
      setWorld(overview);
      setWorlds((current) => [...current.filter((item) => item.id !== overview.id), overview]);
      setShowCreationForm(false);
      void loadNarrativeControlCenter(overview.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建世界胚胎失败');
    } finally {
      setCreating(false);
    }
  }

  async function runStoryArcPlanner() {
    if (!world) return;
    setArcLoading(true);
    setError('');
    try {
      const response = await generateStoryArc(world.id);
      setWorld({ ...world, story_arc: response.story_arc });
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成故事大纲失败');
    } finally {
      setArcLoading(false);
    }
  }

  async function openWorldFromShelf(worldId: number) {
    try {
      await openWorld(worldId);
    } catch (err) {
      setError(err instanceof Error ? err.message : '打开小说失败');
    }
  }

  async function restoreArchivedWorldFromShelf(worldId: number) {
    setArchiveLoading(true);
    setError('');
    try {
      const updated = await updateWorldStatus(worldId, { status: 'active' });
      setWorlds((current) => current.map((item) => (item.id === updated.id ? { ...item, status: updated.status } : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : '恢复写作失败');
    } finally {
      setArchiveLoading(false);
    }
  }

  function returnToBookshelf() {
    setWorld(null);
    setShowCreationForm(false);
    setArchiveError('');
  }

  function startNewWorld() {
    setWorld(null);
    setShowCreationForm(true);
    void loadSeedLibrary();
  }

  async function toggleWorldArchiveStatus() {
    if (!world) return;
    const nextStatus = world.status === 'archived' ? 'active' : 'archived';
    setArchiveLoading(true);
    setArchiveError('');
    try {
      const updated = await updateWorldStatus(world.id, { status: nextStatus });
      setWorld({ ...world, status: updated.status });
      setWorlds((current) => current.map((item) => (item.id === updated.id ? { ...item, status: updated.status } : item)));
    } catch {
      setArchiveError('更新归档状态失败');
    } finally {
      setArchiveLoading(false);
    }
  }

  function launchStoryArcChapter(chapter: StoryArcChapter) {
    if (!world) return;
    const executionContext = buildStoryArcExecutionContext(world, chapter);
    onEnterStudio(world, {
      initialChapterGoal: executionContext.goal,
      executionContext,
    });
  }

  useEffect(() => {
    void loadWorld();
  }, []);

  useEffect(() => {
    if (!loading && autoFocusTitle) titleRef.current?.focus();
  }, [autoFocusTitle, loading, world?.id]);

  const activeWorlds = worlds.filter((item) => item.status !== 'archived');
  const archivedWorlds = worlds.filter((item) => item.status === 'archived');
  const nextStoryArcChapter = world
    ? (world.story_arc.find((chapter) => chapter.chapter_number === world.approved_chapter_count + 1) ?? world.story_arc[0] ?? null)
    : null;
  const isArchivedWorld = world?.status === 'archived';

  if (loading)
    return (
      <p className="p-8 ink-muted" role="status" aria-live="polite">
        正在翻找世界手稿...
      </p>
    );

  if (!world && !showCreationForm) {
    return (
      <section className="px-6 py-8 md:px-10">
        <div className="book-spread p-8 md:p-10">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="chapter-kicker">Bookshelf</p>
              <h1 className="mt-3 text-4xl font-black text-[#34210f]">作品书架</h1>
              <p className="manuscript mt-3 text-sm text-[#5e3b1c]">先给暂缓的小说做快照和 Markdown ZIP，再归档并切换到其他小说继续写。</p>
            </div>
            <button className="primary-button" type="button" onClick={startNewWorld}>创建新小说</button>
          </div>
          {error && <p className="paper-error mt-5" role="alert">{error}</p>}
          <div className="mt-8 grid gap-5 md:grid-cols-2">
            <section className="book-card p-5">
              <h2 className="text-xl font-black text-[#3b2511]">正在创作</h2>
              <div className="mt-4 space-y-3">
                {activeWorlds.length === 0 && <p className="ink-muted text-sm">暂无活跃小说，可创建新小说或恢复已归档作品。</p>}
                {activeWorlds.map((item) => (
                  <article key={item.id} className="rounded-2xl bg-amber-50/60 p-3">
                    <p className="font-black text-[#34210f]">{item.title}</p>
                    <p className="ink-muted mt-1 text-sm">v{item.world_version} · {item.genre_template} · {item.status}</p>
                    <button className="secondary-button mt-3" type="button" onClick={() => void openWorldFromShelf(item.id)}>打开 {item.title}</button>
                  </article>
                ))}
              </div>
            </section>
            <section className="book-card p-5">
              <h2 className="text-xl font-black text-[#3b2511]">已归档</h2>
              <p className="ink-muted mt-2 text-sm">归档只改变书架分组，不会删除世界、章节、快照或导出。</p>
              <div className="mt-4 space-y-3">
                {archivedWorlds.length === 0 && <p className="ink-muted text-sm">暂无归档小说。</p>}
                {archivedWorlds.map((item) => (
                  <article key={item.id} className="rounded-2xl bg-white/40 p-3">
                    <p className="font-black text-[#34210f]">{item.title}</p>
                    <p className="ink-muted mt-1 text-sm">v{item.world_version} · {item.genre_template} · archived</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button className="secondary-button" type="button" onClick={() => void openWorldFromShelf(item.id)}>打开 {item.title}</button>
                      <button className="primary-button" type="button" disabled={archiveLoading} onClick={() => void restoreArchivedWorldFromShelf(item.id)}>恢复写作 {item.title}</button>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </div>
        </div>
      </section>
    );
  }

  if (!world) {
    return (
      <section>
        {worlds.length > 0 && (
          <div className="mx-auto mt-8 max-w-5xl px-6">
            <button className="secondary-button" type="button" onClick={returnToBookshelf}>返回作品书架</button>
          </div>
        )}
        {error && (
          <div className="mx-auto mt-8 max-w-5xl px-6">
            <p className="paper-error text-left" role="alert">
              {error}
            </p>
          </div>
        )}
        <WorldCreationForm
          creating={creating}
          onCreate={submitWorld}
          onCreateSample={submitSampleWorld}
          seeds={seedLibrary}
          seedLoading={seedLibraryLoading}
          seedError={seedLibraryError}
          onLoadSeed={getWorldSeed}
          onCreateSeed={submitSeedWorld}
        />
      </section>
    );
  }

  return (
    <section className="px-6 py-8 md:px-10">
      <div className="book-spread p-8 md:p-10">
        {/* Tab bar */}
        <nav className="mb-8 flex flex-wrap gap-1 rounded-full border border-amber-900/15 bg-amber-50/50 p-1">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex-1 rounded-full px-4 py-2 text-sm font-bold transition-colors ${
                tab === t.key
                  ? 'bg-amber-900 text-amber-50 shadow-sm'
                  : 'text-amber-900/70 hover:bg-amber-100'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>

        {/* Tab content */}
        {tab === 'overview' && (
          <div className="grid gap-8 md:grid-cols-[1fr_1fr]">
            <div>
              <p className="chapter-kicker">World Canon</p>
              <h1
                ref={titleRef}
                tabIndex={-1}
                className="mt-3 text-4xl font-black text-[#34210f]"
              >
                {world.title}
              </h1>
              <p className="mt-3 ink-muted">
                第 {world.world_version} 版 · {world.genre_template} · {world.status}
              </p>
              <p className="manuscript mt-8 text-lg">{world.truth_canon}</p>
              {isArchivedWorld ? (
                <ArchivedWorldPauseCard
                  archiveLoading={archiveLoading}
                  onReturnToBookshelf={returnToBookshelf}
                  onRestoreWriting={toggleWorldArchiveStatus}
                />
              ) : (
                <FirstChapterLaunchpad
                  world={world}
                  nextChapter={nextStoryArcChapter}
                  arcLoading={arcLoading}
                  onGenerateArc={runStoryArcPlanner}
                  onLaunchChapter={launchStoryArcChapter}
                />
              )}
              {error && (
                <p className="paper-error mt-5" role="alert">
                  {error}
                </p>
              )}
              <div className="mt-8 rounded-2xl bg-amber-50/70 p-4">
                <p className="text-sm font-bold text-[#5e3b1c]">书架归档</p>
                <p className="manuscript mt-1 text-sm">归档前建议先创建世界快照并导出 Markdown ZIP。</p>
                {archiveError && <p className="paper-error mt-2" role="alert">{archiveError}</p>}
                <div className="mt-3 flex flex-wrap gap-2">
                  {worlds.length > 0 && <button className="secondary-button" type="button" onClick={returnToBookshelf}>返回作品书架</button>}
                  <button className="secondary-button" type="button" disabled={archiveLoading} onClick={toggleWorldArchiveStatus}>
                    {archiveLoading ? '更新中...' : world.status === 'archived' ? '取消归档当前小说' : '归档当前小说'}
                  </button>
                </div>
              </div>
              {!isArchivedWorld && (
                <div className="mt-8 flex flex-wrap gap-3">
                  <button className="primary-button" onClick={() => onEnterStudio(world, {
                    initialChapterGoal: selectedExecutionContext?.goal,
                    executionContext: selectedExecutionContext ?? undefined,
                  })}>
                    进入创作台
                  </button>
                  <button className="secondary-button" disabled={arcLoading} onClick={runStoryArcPlanner}>
                    {arcLoading ? '规划中...' : world.story_arc.length ? '重新生成故事大纲' : '生成故事大纲'}
                  </button>
                </div>
              )}
            </div>
            <div className="space-y-4">
              <article className="book-card p-5">
                <h2 className="text-lg font-black text-[#3b2511]">角色线索</h2>
                <div className="mt-3 space-y-3">
                  {world.characters.map((character) => (
                    <p className="manuscript" key={character.id}>
                      {character.name}：{character.current_goals.join('、')}
                    </p>
                  ))}
                </div>
              </article>
              <article className="book-card p-5">
                <h2 className="text-lg font-black text-[#3b2511]">伏笔笺</h2>
                <div className="mt-3 space-y-3">
                  {world.foreshadows.map((item) => (
                    <p className="manuscript" key={item.id}>
                      {item.title}：{item.status}
                    </p>
                  ))}
                </div>
              </article>
              <article className="book-card p-5">
                <h2 className="text-lg font-black text-[#3b2511]">最近事件</h2>
                <div className="mt-3 space-y-2 ink-muted">
                  {world.recent_events.length === 0 && <p>还没有正式写入的章节事件。</p>}
                  {world.recent_events.map((event) => (
                    <p key={event.id} className="manuscript">
                      {describeEvent(event, world)}
                    </p>
                  ))}
                </div>
              </article>
            </div>
            <section id="story-arc-planner" className="book-card scroll-mt-6 p-5 md:col-span-2">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="chapter-kicker">Story Arc Planner</p>
                  <h2 className="mt-2 text-2xl font-black text-[#34210f]">前 10 章故事弧线</h2>
                </div>
                <p className="ink-muted text-sm">下一章目标会按已批准章节数自动带入创作台。</p>
              </div>
              <nav aria-label="世界模块快速导航" className="mt-4 flex flex-wrap gap-2">
                <a className="rounded-full border border-amber-900/15 bg-amber-100/70 px-3 py-1 text-xs font-bold text-[#5e3b1c] hover:bg-amber-200" href="#story-arc-planner">故事弧线</a>
                <a className="rounded-full border border-amber-900/15 bg-amber-100/70 px-3 py-1 text-xs font-bold text-[#5e3b1c] hover:bg-amber-200" href="#narrative-control-center">叙事控制台</a>
                <a className="rounded-full border border-amber-900/15 bg-amber-100/70 px-3 py-1 text-xs font-bold text-[#5e3b1c] hover:bg-amber-200" href="#world-archive">导出/快照</a>
                <a className="rounded-full border border-amber-900/15 bg-amber-100/70 px-3 py-1 text-xs font-bold text-[#5e3b1c] hover:bg-amber-200" href="#chapter-history">章节历史</a>
              </nav>
              {world.story_arc.length === 0 ? (
                <p className="manuscript mt-4">还没有故事弧线。生成后会自动为创作台填入下一章目标。</p>
              ) : (
                <div className="mt-5 grid gap-2 md:grid-cols-2">
                  {world.story_arc.map((chapter) => (
                    <StoryArcCard
                      key={chapter.chapter_number}
                      chapter={chapter}
                      expanded={expandedStoryArcChapters.includes(chapter.chapter_number)}
                      onToggle={() => setExpandedStoryArcChapters((current) => (
                        current.includes(chapter.chapter_number)
                          ? current.filter((chapterNumber) => chapterNumber !== chapter.chapter_number)
                          : [...current, chapter.chapter_number]
                      ))}
                    />
                  ))}
                </div>
              )}
            </section>

            <section id="narrative-control-center" className="md:col-span-2 space-y-5 scroll-mt-6">
              <div>
                <p className="chapter-kicker">Narrative Console</p>
                <h2 className="mt-2 text-3xl font-black text-[#34210f]">Narrative Control Center</h2>
                <p className="manuscript mt-2 text-sm text-[#5e3b1c]">查看已批准章节历史，并准备下一章目标。</p>
                {isArchivedWorld && (
                  <p className="mt-3 rounded-2xl bg-amber-100/70 p-3 text-sm font-bold text-[#5e3b1c]">
                    已归档小说为只读模式；恢复写作后才能把建议带入创作台。
                  </p>
                )}
                {selectedExecutionContext && <p className="mt-3 rounded-2xl bg-amber-100/70 p-3 text-sm font-bold text-[#5e3b1c]">已设为下一章目标：{selectedExecutionContext.goal}</p>}
              </div>
              <WorldPulsePanel pulse={worldPulse} loading={worldPulseLoading} error={worldPulseError} />
              <ArcPlanPanel arcPlan={arcPlan} loading={arcPlanLoading} error={arcPlanError} />
              <NarrativeHealthPanel health={narrativeHealth} loading={narrativeHealthLoading} error={narrativeHealthError} />
              <OpenThreadsPanel openThreads={openThreads} loading={openThreadsLoading} error={openThreadsError} />
              <NextChapterPrepPanel
                prep={nextPrep}
                loading={nextPrepLoading}
                error={nextPrepError}
                onUseContext={isArchivedWorld ? undefined : setSelectedExecutionContext}
                onEnterStudioWithContext={isArchivedWorld ? undefined : (context) => onEnterStudio(world, {
                  initialChapterGoal: context.goal,
                  executionContext: context,
                })}
              />
              <WorldSearchPanel worldId={world.id} onSearch={searchWorld} onListTags={listWorldTags} onBulkAssignTag={bulkAssignWorldTag} />
              <WorldTagsPanel
                worldId={world.id}
                onListTags={listWorldTags}
                onCreateTag={createWorldTag}
                onLoadTag={getWorldTag}
                onUpdateTag={updateWorldTag}
                onMergeTag={mergeWorldTag}
                onAssignTag={assignWorldTag}
                onBulkAssignTag={bulkAssignWorldTag}
                onUnassignTag={unassignWorldTag}
                onDeleteTag={deleteWorldTag}
              />
              <div id="chapter-history" className="scroll-mt-6">
                <ChapterHistoryPanel
                  history={chapterHistory}
                  loading={chapterHistoryLoading}
                  error={chapterHistoryError}
                  onLoadDetail={(chapterId) => getChapterHistoryDetail(chapterId)}
                />
              </div>
              <WorldTimelinePanel worldId={world.id} onLoadEvents={getWorldEvents} />
              <div id="world-archive" className="scroll-mt-6">
                <WorldArchivePanel
                  onCreateSnapshot={() => createWorldSnapshot(world.id)}
                  onExportMarkdown={() => exportWorldArchiveMarkdown(world.id)}
                  onListSnapshots={() => listWorldSnapshots(world.id)}
                  onCompareSnapshots={compareWorldSnapshots}
                />
              </div>
            </section>
          </div>
        )}

        {tab === 'characters' && <CharacterManager worldId={world.id} onChanged={loadWorld} />}

        {tab === 'relations' && (
          <RelationManager worldId={world.id} characters={world.characters} onChanged={loadWorld} />
        )}

        {tab === 'foreshadows' && (
          <ForeshadowManager worldId={world.id} characters={world.characters} onChanged={loadWorld} />
        )}
      </div>
    </section>
  );
}
