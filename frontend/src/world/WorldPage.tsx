import { useEffect, useRef, useState } from 'react';
import {
  apiRequest,
  assignWorldTag,
  bulkAssignWorldTag,
  compareWorldSnapshots,
  confirmWorldImport,
  createSampleWorld,
  createWorld,
  createWorldFromSeed,
  draftWorldFromBrief,
  createWorldSnapshot,
  createWorldTag,
  deleteWorldTag,
  exportWorldArchiveMarkdown,
  generateStoryArc,
  getActiveChapterSession,
  getArcPlan,
  getChapterHistory,
  getChapterHistoryDetail,
  getNarrativeHealth,
  getNextChapterPrep,
  getOpenThreads,
  getSerialPlan,
  getWorldEvents,
  getWorldPulse,
  getWorldSeed,
  getWorldTag,
  listWorldImports,
  listWorldSeeds,
  listWorldSnapshots,
  listWorldTags,
  mergeWorldTag,
  previewWorldImport,
  previewStyleHandbook,
  searchWorld,
  unassignWorldTag,
  updateWorldStatus,
  updateWorldTag,
} from '../api/client';
import type { ActiveChapterSessionResponse, ArcPlanResponse, ChapterExecutionContext, ChapterHistoryResponse, ImportBatchWithAssetsResponse, NarrativeHealthResponse, NextChapterPrepResponse, OpenThreadsResponse, SerialPlanChapter, SerialPlanResponse, StoryArcChapter, StudioLaunchContext, StyleHandbookReference, WorldCreateRequest, WorldCreationMaterialReference, WorldOverview, WorldPulseResponse, WorldSeedSummary, WorldSummary } from '../api/types';
import { CharacterManager } from '../components/CharacterManager';
import { ForeshadowManager } from '../components/ForeshadowManager';
import { RelationManager } from '../components/RelationManager';
import { ArcPlanPanel } from './ArcPlanPanel';
import { ChapterHistoryPanel } from './ChapterHistoryPanel';
import { buildManualExecutionContext, withStyleHandbookReference } from './chapterExecutionContext';
import { NarrativeHealthPanel } from './NarrativeHealthPanel';
import { NextChapterPrepPanel } from './NextChapterPrepPanel';
import { OpenThreadsPanel } from './OpenThreadsPanel';
import { WorldArchivePanel } from './WorldArchivePanel';
import { WorldCreationForm } from './WorldCreationForm';
import { WorldImportPanel } from './WorldImportPanel';
import { WorldPulsePanel } from './WorldPulsePanel';
import { WorldSearchPanel } from './WorldSearchPanel';
import { WorldTagsPanel } from './WorldTagsPanel';
import { WorldTimelinePanel } from './WorldTimelinePanel';
import { TruthLayersPanel } from './TruthLayersPanel';
import { WorkbenchShell } from '../workbench/WorkbenchShell';
import { labelGenre, labelStatus, labelWorldVersion } from './displayLabels';

type WorldRefreshKey = { worldId: number; token: number };

type Props = {
  onEnterStudio: (world: WorldOverview, context?: StudioLaunchContext) => void;
  autoFocusTitle?: boolean;
  refreshKey?: WorldRefreshKey | null;
};

type Tab = 'overview' | 'write' | 'characters' | 'relations' | 'foreshadows' | 'analysis' | 'archive';

const TABS: { key: Tab; label: string }[] = [
  { key: 'overview', label: '世界概览' },
  { key: 'write', label: '继续创作' },
  { key: 'characters', label: '角色' },
  { key: 'relations', label: '关系' },
  { key: 'foreshadows', label: '伏笔' },
  { key: 'analysis', label: '运营分析' },
  { key: 'archive', label: '归档导出' },
];
import {
    describeEvent,
    isOpenForeshadow,
    openForeshadows,
    buildFirstChapterQuickStartGoal,
    materialReferencesFromImportBatches,
    worldLoadFailureMessage,
    dashboardActions,
    buildStoryArcGoal,
    buildStoryArcExecutionContext,
    buildWorldCreationDraftExecutionContext,
    buildSerialPlanExecutionContext,
    WorldOperationsDashboard,
    StoryArcCard,
    FirstChapterLaunchpad,
    SerialPlanPanel,
    ArchivedWorldPauseCard,
    FirstChapterOnboardingCard,
} from './WorldPageHelpers';


export function WorldPage({ onEnterStudio, autoFocusTitle = true, refreshKey = null }: Props) {
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
  const [chapterHistoryLoaded, setChapterHistoryLoaded] = useState(false);
  const [nextPrep, setNextPrep] = useState<NextChapterPrepResponse | null>(null);
  const [nextPrepLoading, setNextPrepLoading] = useState(false);
  const [nextPrepError, setNextPrepError] = useState('');
  const [nextPrepLoaded, setNextPrepLoaded] = useState(false);
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
  const [serialPlan, setSerialPlan] = useState<SerialPlanResponse | null>(null);
  const [serialPlanLoading, setSerialPlanLoading] = useState(false);
  const [serialPlanError, setSerialPlanError] = useState('');
  const [analysisLoaded, setAnalysisLoaded] = useState(false);
  const [selectedExecutionContext, setSelectedExecutionContext] = useState<ChapterExecutionContext | null>(null);
  const [selectedStyleHandbook, setSelectedStyleHandbook] = useState<StyleHandbookReference | null>(null);
  const [creationMaterialReferences, setCreationMaterialReferences] = useState<WorldCreationMaterialReference[]>([]);
  const [creationMaterialLoading, setCreationMaterialLoading] = useState(false);
  const [creationMaterialError, setCreationMaterialError] = useState('');
  const [worldCreationDraftGoal, setWorldCreationDraftGoal] = useState('');
  const [activeChapterSession, setActiveChapterSession] = useState<ActiveChapterSessionResponse | null>(null);
  const [activeChapterSessionWorldId, setActiveChapterSessionWorldId] = useState<number | null>(null);
  const currentActiveChapterSession = activeChapterSessionWorldId === world?.id ? activeChapterSession : null;
  const [expandedStoryArcChapters, setExpandedStoryArcChapters] = useState<number[]>([]);
  const [tab, setTab] = useState<Tab>('overview');
  const titleRef = useRef<HTMLHeadingElement>(null);

  function resetNarrativeData() {
    setChapterHistory(null);
    setChapterHistoryLoading(false);
    setChapterHistoryError('');
    setChapterHistoryLoaded(false);
    setNextPrep(null);
    setNextPrepLoading(false);
    setNextPrepError('');
    setNextPrepLoaded(false);
    setNarrativeHealth(null);
    setNarrativeHealthLoading(false);
    setNarrativeHealthError('');
    setOpenThreads(null);
    setOpenThreadsLoading(false);
    setOpenThreadsError('');
    setWorldPulse(null);
    setWorldPulseLoading(false);
    setWorldPulseError('');
    setArcPlan(null);
    setArcPlanLoading(false);
    setArcPlanError('');
    setSerialPlan(null);
    setSerialPlanLoading(false);
    setSerialPlanError('');
    setAnalysisLoaded(false);
  }

  function clearActiveChapterSession() {
    setActiveChapterSession(null);
    setActiveChapterSessionWorldId(null);
  }

  function storeActiveChapterSession(worldId: number, session: ActiveChapterSessionResponse) {
    const resumableSession = session.chapter || session.recent_approval ? session : null;
    setActiveChapterSession(resumableSession);
    setActiveChapterSessionWorldId(resumableSession ? worldId : null);
  }

  async function refreshNextPrep(worldId: number) {
    setNextPrepLoading(true);
    setNextPrepError('');
    try {
      setNextPrep(await getNextChapterPrep(worldId));
    } catch {
      setNextPrep(null);
      setNextPrepError('下一章准备台暂不可用');
    } finally {
      setNextPrepLoading(false);
      setNextPrepLoaded(true);
    }
  }

  async function loadWriteData(worldId: number) {
    if (nextPrepLoaded || nextPrepLoading) return;
    await refreshNextPrep(worldId);
  }

  async function loadSerialPlan(worldId: number) {
    setSerialPlanLoading(true);
    setSerialPlanError('');
    try {
      setSerialPlan(await getSerialPlan(worldId, 3));
    } catch (err) {
      setSerialPlanError(err instanceof Error ? err.message : '自动连载试验生成失败');
    } finally {
      setSerialPlanLoading(false);
    }
  }

  async function loadAnalysisData(worldId: number) {
    if (analysisLoaded || worldPulseLoading || arcPlanLoading || narrativeHealthLoading || openThreadsLoading) return;
    setWorldPulseLoading(true);
    setArcPlanLoading(true);
    setNarrativeHealthLoading(true);
    setOpenThreadsLoading(true);
    setWorldPulseError('');
    setArcPlanError('');
    setNarrativeHealthError('');
    setOpenThreadsError('');

    const [pulseResult, arcPlanResult, healthResult, threadsResult] = await Promise.allSettled([
      getWorldPulse(worldId),
      getArcPlan(worldId),
      getNarrativeHealth(worldId),
      getOpenThreads(worldId),
    ]);

    if (pulseResult.status === 'fulfilled') setWorldPulse(pulseResult.value);
    else {
      setWorldPulse(null);
      setWorldPulseError('世界近况暂不可用');
    }

    if (arcPlanResult.status === 'fulfilled') setArcPlan(arcPlanResult.value);
    else {
      setArcPlan(null);
      setArcPlanError('篇章规划暂不可用');
    }

    if (healthResult.status === 'fulfilled') setNarrativeHealth(healthResult.value);
    else {
      setNarrativeHealth(null);
      setNarrativeHealthError('叙事健康度暂不可用');
    }

    if (threadsResult.status === 'fulfilled') setOpenThreads(threadsResult.value);
    else {
      setOpenThreads(null);
      setOpenThreadsError('开放线索看板暂不可用');
    }

    setWorldPulseLoading(false);
    setArcPlanLoading(false);
    setNarrativeHealthLoading(false);
    setOpenThreadsLoading(false);
    setAnalysisLoaded(true);
  }

  async function loadArchiveData(worldId: number) {
    if (chapterHistoryLoaded || chapterHistoryLoading) return;
    setChapterHistoryLoading(true);
    setChapterHistoryError('');
    try {
      setChapterHistory(await getChapterHistory(worldId));
    } catch {
      setChapterHistory(null);
      setChapterHistoryError('章节历史暂不可用');
    } finally {
      setChapterHistoryLoading(false);
      setChapterHistoryLoaded(true);
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
      setSeedLibraryError('灵感模板库暂不可用');
    } finally {
      setSeedLibraryLoading(false);
    }
  }

  async function openWorld(worldId: number) {
    setError('');
    setArchiveError('');
    const [overview, activeSession] = await Promise.all([
      apiRequest<WorldOverview>(`/worlds/${worldId}/overview`),
      getActiveChapterSession(worldId),
    ]);
    resetNarrativeData();
    setWorld(overview);
    storeActiveChapterSession(worldId, activeSession);
    setWorlds((current) => [...current.filter((item) => item.id !== overview.id), overview]);
    setShowCreationForm(false);
    setSelectedExecutionContext(null);
    setCreationMaterialReferences([]);
    setCreationMaterialError('');
    setWorldCreationDraftGoal('');
    setTab('overview');
  }

  async function loadWorld(preferredWorldId?: number) {
    setError('');
    try {
      const loadedWorlds = await apiRequest<WorldSummary[]>('/worlds');
      setWorlds(loadedWorlds);
      const preferredWorld = preferredWorldId === undefined
        ? undefined
        : loadedWorlds.find((item) => item.id === preferredWorldId);
      if (loadedWorlds.length === 0) {
        setWorld(null);
        clearActiveChapterSession();
        setShowCreationForm(true);
        void loadSeedLibrary();
      } else if (preferredWorld) {
        await openWorld(preferredWorld.id);
      } else if (loadedWorlds.length === 1 && loadedWorlds[0].status !== 'archived') {
        await openWorld(loadedWorlds[0].id);
      } else {
        setWorld(null);
        clearActiveChapterSession();
        setShowCreationForm(false);
      }
    } catch (err) {
      setError(worldLoadFailureMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function submitWorld(payload: WorldCreateRequest, context?: { firstChapterGoal?: string }) {
    setCreating(true);
    setError('');
    try {
      const created = await createWorld(payload);
      const overview = await apiRequest<WorldOverview>(`/worlds/${created.id}/overview`);
      resetNarrativeData();
      setWorld(overview);
      setWorlds((current) => [...current.filter((item) => item.id !== overview.id), overview]);
      setShowCreationForm(false);
      clearActiveChapterSession();
      setSelectedExecutionContext(null);
      setCreationMaterialReferences([]);
      setCreationMaterialError('');
      setWorldCreationDraftGoal(context?.firstChapterGoal ?? '');
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
      resetNarrativeData();
      setWorld(overview);
      setWorlds((current) => [...current.filter((item) => item.id !== overview.id), overview]);
      setShowCreationForm(false);
      clearActiveChapterSession();
      setCreationMaterialReferences([]);
      setCreationMaterialError('');
      setWorldCreationDraftGoal('');
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建世界失败');
    } finally {
      setCreating(false);
    }
  }

  async function submitSeedWorld(seedKey: string) {
    const firstChapterGoal = seedLibrary.find((seed) => seed.key === seedKey)?.starter_guidance.first_chapter_goal ?? '';
    setCreating(true);
    setError('');
    try {
      const created = await createWorldFromSeed(seedKey);
      const overview = await apiRequest<WorldOverview>(`/worlds/${created.id}/overview`);
      resetNarrativeData();
      setWorld(overview);
      setWorlds((current) => [...current.filter((item) => item.id !== overview.id), overview]);
      setShowCreationForm(false);
      clearActiveChapterSession();
      setCreationMaterialReferences([]);
      setCreationMaterialError('');
      setWorldCreationDraftGoal(firstChapterGoal);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建灵感模板失败');
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
    clearActiveChapterSession();
    setShowCreationForm(false);
    setArchiveError('');
    setCreationMaterialReferences([]);
    setCreationMaterialError('');
    setWorldCreationDraftGoal('');
  }

  function startNewWorld() {
    setWorld(null);
    clearActiveChapterSession();
    setShowCreationForm(true);
    setCreationMaterialReferences([]);
    setCreationMaterialError('');
    setWorldCreationDraftGoal('');
    void loadSeedLibrary();
  }

  async function startNewWorldWithImportMaterials() {
    if (!world) return;
    setCreationMaterialLoading(true);
    setCreationMaterialError('');
    try {
      const response = await listWorldImports(world.id);
      const references = materialReferencesFromImportBatches(response.batches).slice(0, 6);
      if (references.length === 0) {
        setCreationMaterialError('当前小说还没有可引用的 Import Node 候选素材');
        return;
      }
      setCreationMaterialReferences(references);
      setWorld(null);
      clearActiveChapterSession();
      setShowCreationForm(true);
      setWorldCreationDraftGoal('');
      void loadSeedLibrary();
    } catch (err) {
      setCreationMaterialError(err instanceof Error ? err.message : '读取 Import Node 候选素材失败');
    } finally {
      setCreationMaterialLoading(false);
    }
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

  function withActiveStyleHandbook(context: ChapterExecutionContext): ChapterExecutionContext {
    return selectedStyleHandbook ? withStyleHandbookReference(context, selectedStyleHandbook) : context;
  }

  function resumeActiveChapterIfPresent(): boolean {
    if (!currentActiveChapterSession?.chapter) return false;
    resumeActiveChapter();
    return true;
  }

  function launchStoryArcChapter(chapter: StoryArcChapter) {
    if (!world || resumeActiveChapterIfPresent()) return;
    const executionContext = withActiveStyleHandbook(buildStoryArcExecutionContext(world, chapter));
    onEnterStudio(world, {
      initialChapterGoal: executionContext.goal,
      executionContext,
    });
  }

  function launchSerialPlanChapter(chapter: SerialPlanChapter) {
    if (!world || !serialPlan || resumeActiveChapterIfPresent()) return;
    const executionContext = withActiveStyleHandbook(buildSerialPlanExecutionContext(
      world,
      chapter,
      serialPlan.convergence_guidance,
      serialPlan.review_guardrails,
    ));
    onEnterStudio(world, {
      initialChapterGoal: executionContext.goal,
      executionContext,
    });
  }

  function launchFirstChapterQuickStart() {
    if (!world || resumeActiveChapterIfPresent()) return;
    const hasWorldCreationDraftGoal = Boolean(worldCreationDraftGoal);
    const goal = worldCreationDraftGoal || buildFirstChapterQuickStartGoal(world);
    const executionContext = withActiveStyleHandbook(
      hasWorldCreationDraftGoal
        ? buildWorldCreationDraftExecutionContext(world, goal)
        : {
            ...buildManualExecutionContext(world, goal),
            source_signals: ['first_chapter_quick_start'],
          },
    );
    onEnterStudio(world, {
      initialChapterGoal: goal,
      executionContext,
      autoDraftFirstChapter: true,
    });
  }

  function resumeActiveChapter() {
    if (!world || !currentActiveChapterSession?.chapter) return;
    const activeChapter = currentActiveChapterSession.chapter;
    onEnterStudio(world, {
      initialChapterGoal: activeChapter.chapter_goal ?? undefined,
      executionContext: activeChapter.execution_context ?? undefined,
      autoDraftFirstChapter: !currentActiveChapterSession.draft,
      resumeSession: currentActiveChapterSession,
    });
  }

  function viewRecentApprovalSettlement() {
    if (!world || !currentActiveChapterSession?.recent_approval) return;
    onEnterStudio(world, { recentApproval: currentActiveChapterSession.recent_approval });
  }

  useEffect(() => {
    void loadWorld(refreshKey?.worldId);
  }, [refreshKey?.token, refreshKey?.worldId]);

  useEffect(() => {
    if (!loading && autoFocusTitle) titleRef.current?.focus();
  }, [autoFocusTitle, loading, world?.id]);

  useEffect(() => {
    if (!world) return;
    if (tab === 'write') void loadWriteData(world.id);
    if (tab === 'analysis') void loadAnalysisData(world.id);
    if (tab === 'archive') void loadArchiveData(world.id);
  }, [tab, world?.id]);

  const activeWorlds = worlds.filter((item) => item.status !== 'archived');
  const archivedWorlds = worlds.filter((item) => item.status === 'archived');
  const nextStoryArcChapter = world
    ? (world.story_arc.find((chapter) => chapter.chapter_number === world.approved_chapter_count + 1) ?? world.story_arc[0] ?? null)
    : null;
  const isArchivedWorld = world?.status === 'archived';
  const firstChapterQuickStartGoal = world
    ? worldCreationDraftGoal || buildFirstChapterQuickStartGoal(world)
    : '';
  const shouldShowFirstChapterOnboarding = Boolean(world && !isArchivedWorld && world.approved_chapter_count === 0 && world.story_arc.length === 0);

  if (loading)
    return (
      <WorkbenchShell
        mainLabel="作品书架"
        main={
          <p className="ink-muted" role="status" aria-live="polite">
            正在翻找世界手稿...
          </p>
        }
      />
    );

  if (!world && !showCreationForm) {
    return (
      <WorkbenchShell
        mainLabel="作品书架"
        main={
          <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="chapter-kicker">书架总览</p>
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
                    <p className="ink-muted mt-1 text-sm">{labelWorldVersion(item.world_version)} · {labelGenre(item.genre_template)} · {labelStatus(item.status)}</p>
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
                    <p className="ink-muted mt-1 text-sm">{labelWorldVersion(item.world_version)} · {labelGenre(item.genre_template)} · 已归档</p>
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
        }
      />
    );
  }

  if (!world) {
    return (
      <WorkbenchShell
        navLabel="世界模块"
        mainLabel="创建世界"
        nav={
          worlds.length > 0 ? (
            <button type="button" className="workbench-nav-item" onClick={returnToBookshelf}>返回作品书架</button>
          ) : null
        }
        main={
          <div className="space-y-4">
            {error && (
              <p className="paper-error text-left" role="alert">
                {error}
              </p>
            )}
            <WorldCreationForm
          creating={creating}
          onCreate={submitWorld}
          onCreateSample={submitSampleWorld}
          onDraftFromBrief={draftWorldFromBrief}
          activeStyleHandbook={selectedStyleHandbook}
          materialReferences={creationMaterialReferences}
          seeds={seedLibrary}
          seedLoading={seedLibraryLoading}
          seedError={seedLibraryError}
          onLoadSeed={getWorldSeed}
          onCreateSeed={submitSeedWorld}
            />
          </div>
        }
      />
    );
  }

  return (
    <WorkbenchShell
      navLabel="世界模块"
      mainLabel="世界内容"
      nav={
        <div className="space-y-4">
        <nav className="workbench-stack-nav" aria-label="世界模块">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={tab === t.key ? 'workbench-nav-item is-active' : 'workbench-nav-item'}
            >
              {t.label}
            </button>
          ))}
        </nav>
          {worlds.length > 0 && (
            <button className="workbench-nav-item" type="button" onClick={returnToBookshelf}>返回作品书架</button>
          )}
        </div>
      }
      main={
        <>
        {tab === 'overview' && (
          <div className="space-y-8">
            <div>
              <p className="chapter-kicker">世界正史档案</p>
              <h1
                ref={titleRef}
                tabIndex={-1}
                className="mt-3 text-4xl font-black text-[#34210f]"
              >
                {world.title}
              </h1>
              <p className="mt-3 ink-muted">
                {labelWorldVersion(world.world_version)} · {labelGenre(world.genre_template)} · {labelStatus(world.status)}
              </p>
              <p className="manuscript mt-8 text-lg">{world.truth_canon}</p>
              <div className="mt-8">
                <TruthLayersPanel world={world} onChanged={loadWorld} readOnly={isArchivedWorld} />
              </div>
              {currentActiveChapterSession?.chapter && !isArchivedWorld && (
                <article className="mt-6 rounded-3xl border-2 border-amber-900/20 bg-amber-100/80 p-5 shadow-sm" aria-label="进行中章节入口">
                  <p className="chapter-kicker">Studio 草稿已保留</p>
                  <h2 className="mt-2 text-2xl font-black text-[#34210f]">继续{currentActiveChapterSession.draft ? '审阅' : '生成'}「{currentActiveChapterSession.chapter.title}」</h2>
                  <p className="manuscript mt-2 text-sm text-[#5e3b1c]">已恢复到 {currentActiveChapterSession.chapter.status} 阶段；不会创建重复章节，也不会自动写入正史或推进世界进度。</p>
                  <button className="primary-button mt-4" type="button" onClick={resumeActiveChapter}>继续进入 Studio</button>
                </article>
              )}
              {currentActiveChapterSession?.recent_approval && !currentActiveChapterSession.chapter && (
                <article className="mt-6 rounded-3xl border-2 border-emerald-700/20 bg-emerald-50/80 p-5 shadow-sm" aria-label="最近世界推进结算入口">
                  <p className="chapter-kicker">最近正史结算</p>
                  <h2 className="mt-2 text-2xl font-black text-[#203b20]">查看「{currentActiveChapterSession.recent_approval.title}」的世界推进结算</h2>
                  <p className="manuscript mt-2 text-sm text-emerald-950">本章已写入正史并推进到第 {currentActiveChapterSession.recent_approval.world_version_after} 版。这里只恢复只读结算，不会再次批准或写入任何世界变化。</p>
                  <button className="primary-button mt-4" type="button" onClick={viewRecentApprovalSettlement}>查看最近世界推进结算</button>
                </article>
              )}
              {worldCreationDraftGoal && !currentActiveChapterSession?.chapter && !isArchivedWorld && (
                <article className="mt-6 rounded-3xl border-2 border-amber-900/20 bg-amber-100/80 p-5 shadow-sm" aria-label="创建草稿第一章入口">
                  <p className="chapter-kicker">创建草稿</p>
                  <h2 className="mt-2 text-2xl font-black text-[#34210f]">生成第一章草稿并进入 Studio</h2>
                  <p className="manuscript mt-2 text-sm text-[#5e3b1c]">第一章目标：{worldCreationDraftGoal}</p>
                  <p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">只会在 Studio 创建章节草稿与审批预览；确认前不会写入正史或推进世界进度。</p>
                  <button className="primary-button mt-4" type="button" onClick={launchFirstChapterQuickStart}>生成第一章草稿并进入 Studio</button>
                </article>
              )}
              {shouldShowFirstChapterOnboarding && !worldCreationDraftGoal && !currentActiveChapterSession?.chapter && (
                <FirstChapterOnboardingCard
                  arcLoading={arcLoading}
                  quickStartGoal={firstChapterQuickStartGoal}
                  onQuickStart={launchFirstChapterQuickStart}
                  onGenerateArc={runStoryArcPlanner}
                  onOpenWriteTab={() => setTab('write')}
                />
              )}
              <WorldOperationsDashboard
                world={world}
                isArchivedWorld={isArchivedWorld}
                hasActiveChapter={Boolean(currentActiveChapterSession?.chapter)}
                onContinue={() => {
                  if (resumeActiveChapterIfPresent()) return;
                  const baseContext = selectedExecutionContext
                    ?? (selectedStyleHandbook ? buildManualExecutionContext(world, '') : undefined);
                  onEnterStudio(world, {
                    initialChapterGoal: selectedExecutionContext?.goal,
                    executionContext: baseContext ? withActiveStyleHandbook(baseContext) : undefined,
                  });
                }}
                onShowForeshadows={() => setTab('foreshadows')}
                onShowArchive={() => setTab('archive')}
              />
              {isArchivedWorld && (
                <ArchivedWorldPauseCard
                  archiveLoading={archiveLoading}
                  onReturnToBookshelf={returnToBookshelf}
                  onRestoreWriting={toggleWorldArchiveStatus}
                />
              )}
              {error && (
                <p className="paper-error mt-5" role="alert">
                  {error}
                </p>
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
                      {item.title}：{labelStatus(item.status)}
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
          </div>
        )}

        {tab === 'write' && !isArchivedWorld && (
          <div className="space-y-6">
            <FirstChapterLaunchpad
              world={world}
              nextChapter={nextStoryArcChapter}
              arcLoading={arcLoading}
              onGenerateArc={runStoryArcPlanner}
              onLaunchChapter={launchStoryArcChapter}
              quickStartGoal={firstChapterQuickStartGoal}
              onQuickStart={launchFirstChapterQuickStart}
            />
            <SerialPlanPanel
              serialPlan={serialPlan}
              loading={serialPlanLoading}
              error={serialPlanError}
              onGenerate={() => void loadSerialPlan(world.id)}
              onLaunchChapter={launchSerialPlanChapter}
            />
            <NextChapterPrepPanel
              prep={nextPrep}
              loading={nextPrepLoading}
              error={nextPrepError}
              onUseContext={setSelectedExecutionContext}
              onEnterStudioWithContext={(context) => {
                if (resumeActiveChapterIfPresent()) return;
                onEnterStudio(world, {
                  initialChapterGoal: context.goal,
                  executionContext: withActiveStyleHandbook(context),
                });
              }}
            />
            <WorldImportPanel
              worldId={world.id}
              readOnly={isArchivedWorld}
              onPreview={previewWorldImport}
              onPreviewStyleHandbook={previewStyleHandbook}
              onUseStyleHandbook={setSelectedStyleHandbook}
              onConfirm={confirmWorldImport}
              onListBatches={listWorldImports}
              onConfirmed={() => void refreshNextPrep(world.id)}
            />
            <div className="rounded-2xl bg-amber-50/80 p-4">
              <p className="text-sm font-black text-[#3b2511]">用 Import Node 候选素材开新书</p>
              <p className="manuscript mt-1 text-sm text-[#5e3b1c]">只把候选素材标题、摘要、素材池和来源权利带入一句话开书作为只读写作参考；不带入原文，不会创建世界、不会写入 canon/正史或 EventLog。</p>
              <button className="secondary-button mt-3" type="button" disabled={creationMaterialLoading} onClick={() => void startNewWorldWithImportMaterials()}>
                {creationMaterialLoading ? '读取候选素材中...' : '用候选素材开新书草稿'}
              </button>
              {creationMaterialError && <p className="paper-error mt-3" role="alert">{creationMaterialError}</p>}
            </div>
            {selectedStyleHandbook && (
              <p className="rounded-2xl bg-amber-50/80 p-3 text-sm font-bold text-[#5e3b1c]" data-testid="active-style-handbook">
                已设为写作风格参考：{selectedStyleHandbook.source_title}（仅抽象维度，不写入正史）
                <button type="button" className="ml-3 underline" onClick={() => setSelectedStyleHandbook(null)}>取消</button>
              </p>
            )}
            {selectedExecutionContext && <p className="rounded-2xl bg-amber-100/70 p-3 text-sm font-bold text-[#5e3b1c]">已设为下一章目标：{selectedExecutionContext.goal}</p>}
            <section className="book-card scroll-mt-6 p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="chapter-kicker">故事大纲</p>
                  <h2 className="mt-2 text-2xl font-black text-[#34210f]">前 10 章故事弧线</h2>
                </div>
                <p className="ink-muted text-sm">下一章目标会按已批准章节数自动带入创作台。</p>
              </div>
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
          </div>
        )}

        {tab === 'write' && isArchivedWorld && (
          <div className="space-y-6">
            <ArchivedWorldPauseCard
              archiveLoading={archiveLoading}
              onReturnToBookshelf={returnToBookshelf}
              onRestoreWriting={toggleWorldArchiveStatus}
            />
            <NextChapterPrepPanel
              prep={nextPrep}
              loading={nextPrepLoading}
              error={nextPrepError}
            />
            <WorldImportPanel
              worldId={world.id}
              readOnly={isArchivedWorld}
              onPreview={previewWorldImport}
              onPreviewStyleHandbook={previewStyleHandbook}
              onConfirm={confirmWorldImport}
              onListBatches={listWorldImports}
              onConfirmed={() => void refreshNextPrep(world.id)}
            />
          </div>
        )}

        {tab === 'characters' && <CharacterManager worldId={world.id} onChanged={loadWorld} readOnly={isArchivedWorld} />}

        {tab === 'relations' && (
          <RelationManager worldId={world.id} characters={world.characters} onChanged={loadWorld} readOnly={isArchivedWorld} />
        )}

        {tab === 'foreshadows' && (
          <ForeshadowManager worldId={world.id} characters={world.characters} onChanged={loadWorld} readOnly={isArchivedWorld} />
        )}

        {tab === 'analysis' && (
          <section className="space-y-5">
            <div>
              <p className="chapter-kicker">故事管理</p>
              <h2 className="mt-2 text-3xl font-black text-[#34210f]">故事运营分析</h2>
              <p className="manuscript mt-2 text-sm text-[#5e3b1c]">查看故事近况、风险和开放线索，决定下一步优先处理什么。</p>
            </div>
            <WorldPulsePanel pulse={worldPulse} loading={worldPulseLoading} error={worldPulseError} />
            <ArcPlanPanel arcPlan={arcPlan} loading={arcPlanLoading} error={arcPlanError} />
            <NarrativeHealthPanel health={narrativeHealth} loading={narrativeHealthLoading} error={narrativeHealthError} />
            <OpenThreadsPanel openThreads={openThreads} loading={openThreadsLoading} error={openThreadsError} />
          </section>
        )}

        {tab === 'archive' && (
          <section className="space-y-5">
            <div>
              <p className="chapter-kicker">档案管理</p>
              <h2 className="mt-2 text-3xl font-black text-[#34210f]">档案与导出</h2>
              <p className="manuscript mt-2 text-sm text-[#5e3b1c]">查看章节历史、时间线、标签和搜索结果，并管理快照与导出。</p>
              {isArchivedWorld && (
                <p className="mt-3 rounded-2xl bg-amber-100/70 p-3 text-sm font-bold text-[#5e3b1c]">
                  已归档小说为只读模式；可继续查看和导出档案，恢复写作后才能创建新快照。
                </p>
              )}
            </div>
            <ChapterHistoryPanel
              history={chapterHistory}
              loading={chapterHistoryLoading}
              error={chapterHistoryError}
              onLoadDetail={(chapterId) => getChapterHistoryDetail(chapterId)}
            />
            <WorldTimelinePanel worldId={world.id} onLoadEvents={getWorldEvents} />
            <WorldSearchPanel worldId={world.id} readOnly={isArchivedWorld} onSearch={searchWorld} onListTags={listWorldTags} onBulkAssignTag={bulkAssignWorldTag} />
            <WorldTagsPanel
              worldId={world.id}
              readOnly={isArchivedWorld}
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
            <WorldArchivePanel
              readOnly={isArchivedWorld}
              onCreateSnapshot={() => createWorldSnapshot(world.id)}
              onExportMarkdown={() => exportWorldArchiveMarkdown(world.id)}
              onListSnapshots={() => listWorldSnapshots(world.id)}
              onCompareSnapshots={compareWorldSnapshots}
            />
            <div className="rounded-2xl bg-amber-50/70 p-4">
              <p className="text-sm font-bold text-[#5e3b1c]">书架归档</p>
              <p className="manuscript mt-1 text-sm">归档前建议先创建世界快照并导出 Markdown ZIP。</p>
              {archiveError && <p className="paper-error mt-2" role="alert">{archiveError}</p>}
              <div className="mt-3 flex flex-wrap gap-2">
                <button className="secondary-button" type="button" disabled={archiveLoading} onClick={toggleWorldArchiveStatus}>
                  {archiveLoading ? '更新中...' : world.status === 'archived' ? '取消归档当前小说' : '归档当前小说'}
                </button>
              </div>
            </div>
          </section>
        )}
        </>
      }
    />
  );
}
