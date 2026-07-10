import { useEffect, useRef, useState } from 'react';
import {
  apiRequest,
  approveChapter,
  checkApprovalConsistency,
  createChapter as createChapterRequest,
  editDraft as editDraftRequest,
  generateCharacterArcReport,
  generateCriticReport,
  generateOutline,
  getApprovalPreview,
  getApprovalReadiness,
  getChapterHistoryDetail,
  getDraftDiff,
  getDraftVersion,
  exportWorldArchiveMarkdown,
  rejectDraft as rejectDraftRequest,
  reviseDraft,
  reviseParagraph,
  stashDraft,
  suggestGoal,
  writeChapter,
} from '../api/client';
import type { ApprovalPreviewResponse, ApprovalReadinessResponse, BeatCard, ChapterExecutionContext, ChapterPipelineResponse, CharacterArcReportResponse, ConsistencySummary, ConsistencyWarning, CriticReportResponse, DraftDiffResponse, DraftResponse, StudioLaunchContext, WorldOverview } from '../api/types';
import { withEditedGoal } from '../world/chapterExecutionContext';
import { ApprovalReadinessPanel } from './ApprovalReadinessPanel';
import { CharacterArcPanel } from './CharacterArcPanel';
import { CriticReportPanel } from './CriticReportPanel';

type Props = { world: WorldOverview; launchContext?: StudioLaunchContext; onBack: () => void; onApproved: (world: WorldOverview) => void };

type WorldSettlement = {
  worldBefore: number;
  worldAfter: number;
  approvedChapterCount: number;
  characterChangeCount: number;
  foreshadowChangeCount: number;
  hasChapterApprovedEvent: boolean;
  overview: WorldOverview;
  exportMessage?: string;
  exportError?: string;
};

function dialogueToText(beat: BeatCard): string {
  return beat.key_dialogue_hints.join('\n');
}

function textToDialogue(value: string): string[] {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

function sourceLabel(source: ChapterExecutionContext['source']): string {
  return source === 'next_chapter_prep' ? '下一章准备台' : '手动';
}

function names(values: Array<{ name?: string; title?: string }>): string {
  return values.map((value) => value.name ?? value.title).filter(Boolean).join('、') || '无';
}

function autoDraftFailureMessage(error: unknown): string {
  const recoveryMessage = '第一章草稿暂未生成。已创建的世界和当前创作进度都已保留，可以直接重试。';
  const detail = error instanceof Error ? error.message.trim() : '';
  if (!detail || /^[A-Z][A-Z0-9_]+$/.test(detail)) return recoveryMessage;
  return `${recoveryMessage} 原因：${detail}`;
}

function ExecutionContextSummary({ context, frozen }: { context?: ChapterExecutionContext | null; frozen?: boolean }) {
  if (!context) {
    return (
      <div className="book-card p-5">
        <h2 className="font-black text-[#3b2511]">本章设定（本章要写什么）</h2>
        <p className="mt-3 ink-muted">本章暂无来自下一章准备台的设定。创建章节时会根据当前目标生成手动设定快照。</p>
      </div>
    );
  }
  return (
    <div className="book-card p-5">
      <h2 className="font-black text-[#3b2511]">本章设定（本章要写什么）</h2>
      {frozen && <p className="mt-2 text-sm font-bold text-[#5e3b1c]">已冻结本章设定：{context.source} · v{context.source_world_version}</p>}
      <p className="mt-3 ink-muted">来源：{sourceLabel(context.source)}</p>
      <p className="mt-2 ink-muted">源世界版本：v{context.source_world_version}</p>
      <p className="mt-2 ink-muted">建议章节：第 {context.next_chapter_number ?? '?'} 章</p>
      <p className="mt-2 ink-muted">推荐 POV：{context.recommended_pov.name ?? '暂无'}</p>
      <p className="mt-2 ink-muted">优先角色：{names(context.priority_characters)}</p>
      <p className="mt-2 ink-muted">优先伏笔：{names(context.priority_foreshadows)}</p>
      <p className="mt-2 ink-muted">推进提示：{context.progression_hints.length} 条</p>
      <p className="mt-2 ink-muted">连续性提醒：{context.continuity_warnings.length} 条</p>
      {context.continuity_warnings.length > 0 && (
        <ul className="mt-3 space-y-2 rounded-xl bg-amber-50/70 p-3 text-sm text-[#5e3b1c]" aria-label="连续性提醒列表">
          {context.continuity_warnings.map((warning, index) => (
            <li key={`${warning.category}-${index}`}>{warning.message}</li>
          ))}
        </ul>
      )}
      {context.style_handbook_reference && (
        <p className="mt-2 ink-muted">写作风格参考：{context.style_handbook_reference.source_title}（仅抽象风格维度，不写入正史）</p>
      )}
    </div>
  );
}

function ExecutionContextSnapshot({ context }: { context?: ChapterExecutionContext | null }) {
  if (!context) return null;
  return (
    <section className="space-y-3 rounded-2xl bg-white/35 p-4">
      <h3 className="font-black text-[#3b2511]">本章设定快照</h3>
      <p className="manuscript text-sm">来源：{sourceLabel(context.source)} · v{context.source_world_version}</p>
      <p className="manuscript text-sm">目标：{context.goal}</p>
      <p className="manuscript text-sm">推荐 POV：{context.recommended_pov.name ?? '暂无'}</p>
      <p className="manuscript text-sm">优先角色：{names(context.priority_characters)}</p>
      <p className="manuscript text-sm">优先伏笔：{names(context.priority_foreshadows)}</p>
      {context.progression_hints.map((hint) => (
        <p key={hint.title} className="manuscript text-sm">推进提示：{hint.title}</p>
      ))}
      {context.continuity_warnings.map((warning, index) => (
        <p key={`${warning.category}-${index}`} className="manuscript text-sm">连续性提醒：{warning.message}</p>
      ))}
      {context.style_handbook_reference && (
        <div className="rounded-xl bg-amber-50/60 p-3" data-testid="execution-style-handbook">
          <p className="manuscript text-sm font-bold">写作风格参考：{context.style_handbook_reference.source_title}</p>
          <p className="manuscript text-xs ink-muted">仅参考抽象风格维度（节奏/语言密度/对白比例等），不写入正史，禁止照搬原文。</p>
        </div>
      )}
    </section>
  );
}

export function StudioPage({ world, launchContext, onBack, onApproved }: Props) {
  const resumedChapter = launchContext?.resumeSession?.chapter ?? null;
  const resumedDraft = launchContext?.resumeSession?.draft ?? null;
  const recentApproval = launchContext?.recentApproval ?? null;
  const [localWorld, setLocalWorld] = useState(world);
  const [goal, setGoal] = useState(launchContext?.initialChapterGoal ?? resumedChapter?.chapter_goal ?? '');
  const [executionContext] = useState(launchContext?.executionContext ?? resumedChapter?.execution_context ?? undefined);
  const [chapter, setChapter] = useState<ChapterPipelineResponse | null>(resumedChapter);
  const [outlineBeats, setOutlineBeats] = useState<BeatCard[]>(resumedChapter?.outline_beats ?? []);
  const [outlineContext, setOutlineContext] = useState<Record<string, unknown>>(resumedChapter?.outline_context ?? {});
  const [draft, setDraft] = useState<DraftResponse | null>(resumedDraft);
  const [draftVersions, setDraftVersions] = useState<number[]>(launchContext?.resumeSession?.draft_versions ?? (resumedDraft ? [resumedDraft.draft_version] : []));
  const [draftDiff, setDraftDiff] = useState<DraftDiffResponse | null>(null);
  const [approvalPreview, setApprovalPreview] = useState<ApprovalPreviewResponse | null>(null);
  const [selectedCharacterChangeIndexes, setSelectedCharacterChangeIndexes] = useState<number[]>([]);
  const [selectedForeshadowChangeIndexes, setSelectedForeshadowChangeIndexes] = useState<number[]>([]);
  const [consistencySummary, setConsistencySummary] = useState<ConsistencySummary | null>(null);
  const [consistencyWarnings, setConsistencyWarnings] = useState<ConsistencyWarning[]>([]);
  const [approvalReadiness, setApprovalReadiness] = useState<ApprovalReadinessResponse | null>(null);
  const [reviewPanelsLoading, setReviewPanelsLoading] = useState(Boolean(resumedDraft));
  const [reviewPanelsError, setReviewPanelsError] = useState('');
  const [consistencyChecking, setConsistencyChecking] = useState(false);
  const [consistencyValidated, setConsistencyValidated] = useState(false);
  const [critique, setCritique] = useState<CriticReportResponse | null>(null);
  const [characterArcReport, setCharacterArcReport] = useState<CharacterArcReportResponse | null>(null);
  const [settlement, setSettlement] = useState<WorldSettlement | null>(recentApproval ? {
    worldBefore: recentApproval.world_version_before,
    worldAfter: recentApproval.world_version_after,
    approvedChapterCount: world.approved_chapter_count,
    characterChangeCount: recentApproval.character_change_count,
    foreshadowChangeCount: recentApproval.foreshadow_change_count,
    hasChapterApprovedEvent: true,
    overview: world,
  } : null);
  const [approvalCommitState, setApprovalCommitState] = useState<'idle' | 'unknown' | 'committed'>('idle');
  const [settlementSyncError, setSettlementSyncError] = useState('');
  const [latestDraftVersion, setLatestDraftVersion] = useState<number | null>(resumedDraft?.draft_version ?? null);
  const [revisionInstruction, setRevisionInstruction] = useState('');
  const [working, setWorking] = useState(false);
  const [autoDrafting, setAutoDrafting] = useState(false);
  const [operationHint, setOperationHint] = useState('');
  const [suggestingGoal, setSuggestingGoal] = useState(false);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const titleRef = useRef<HTMLHeadingElement>(null);
  const draftTitleRef = useRef<HTMLHeadingElement>(null);
  const autoDraftStartedRef = useRef(false);
  const resumedDraftPanelsLoadedRef = useRef(false);
  const reviewPanelsRequestRef = useRef(0);
  const consistencyRequestRef = useRef(0);
  const approvalSelectionInitializedRef = useRef(false);

  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  useEffect(() => {
    setLocalWorld(world);
  }, [world]);

  useEffect(() => {
    if (launchContext?.initialChapterGoal || chapter || goal.trim().length > 0) return;
    const nextChapterNumber = localWorld.approved_chapter_count + 1;
    const nextArcChapter = localWorld.story_arc.find((item) => item.chapter_number === nextChapterNumber);
    if (nextArcChapter) setGoal(nextArcChapter.summary);
  }, [chapter, goal, launchContext?.initialChapterGoal, localWorld.approved_chapter_count, localWorld.story_arc]);

  useEffect(() => {
    if (draft) draftTitleRef.current?.focus();
  }, [draft]);

  useEffect(() => {
    if (!resumedDraft || resumedDraftPanelsLoadedRef.current) return;
    resumedDraftPanelsLoadedRef.current = true;
    void refreshReviewStudioPanels(resumedDraft);
  }, [resumedDraft]);

  useEffect(() => {
    if (!launchContext?.autoDraftFirstChapter || autoDraftStartedRef.current || draft || !goal.trim()) return;
    autoDraftStartedRef.current = true;
    void autoDraftFirstChapterSession();
  }, [draft, goal, launchContext?.autoDraftFirstChapter]);

  function paragraphList(content: string): string[] {
    return content.split('\n\n').map((paragraph) => paragraph.trim()).filter(Boolean);
  }

  function resolveDraftVersion(nextDraft: DraftResponse): number {
    const draftVersion = Number(nextDraft.draft_version);
    if (Number.isFinite(draftVersion) && draftVersion > 0) return draftVersion;
    const chapterVersion = Number(chapter?.draft_version);
    if (Number.isFinite(chapterVersion) && chapterVersion > 0) return chapterVersion;
    return 1;
  }

  function normalizeDraft(nextDraft: DraftResponse): DraftResponse {
    return { ...nextDraft, draft_version: resolveDraftVersion(nextDraft) };
  }

  function previewIndex(change: { change_index?: number }, fallback: number): number {
    return typeof change.change_index === 'number' ? change.change_index : fallback;
  }

  function toggleIndex(values: number[], index: number): number[] {
    return values.includes(index) ? values.filter((value) => value !== index) : [...values, index].sort((a, b) => a - b);
  }

  function initializeApprovalSelection(preview: ApprovalPreviewResponse) {
    setSelectedCharacterChangeIndexes(preview.character_changes.map((change, index) => previewIndex(change, index)));
    setSelectedForeshadowChangeIndexes(preview.foreshadow_changes.map((change, index) => previewIndex(change, index)));
    approvalSelectionInitializedRef.current = true;
  }

  function clearApprovalSelection() {
    setSelectedCharacterChangeIndexes([]);
    setSelectedForeshadowChangeIndexes([]);
    approvalSelectionInitializedRef.current = false;
  }

  function clearApprovalConsistency() {
    setConsistencySummary(null);
    setConsistencyWarnings([]);
    setConsistencyValidated(false);
  }

  function setPreviewConsistency(preview: ApprovalPreviewResponse) {
    setConsistencySummary(preview.consistency_summary);
    setConsistencyWarnings(preview.consistency_warnings);
    setConsistencyValidated(true);
  }

  function consistencyLabel(summary: ConsistencySummary): string {
    if (summary.status === 'blocked') return '存在阻塞项';
    if (summary.status === 'needs_review') return '存在需复核项';
    return '一致性检查通过';
  }

  async function refreshApprovalConsistency(nextDraft: DraftResponse, characterIndexes: number[], foreshadowIndexes: number[]) {
    const requestId = ++consistencyRequestRef.current;
    setConsistencyChecking(true);
    setConsistencyValidated(false);
    try {
      const result = await checkApprovalConsistency(nextDraft.chapter_id, {
        draft_version: resolveDraftVersion(nextDraft),
        selected_character_change_indexes: characterIndexes,
        selected_foreshadow_change_indexes: foreshadowIndexes,
      });
      if (consistencyRequestRef.current !== requestId) return;
      setConsistencySummary(result.consistency_summary);
      setConsistencyWarnings(result.consistency_warnings);
      setConsistencyValidated(true);
    } catch (err) {
      if (consistencyRequestRef.current === requestId) {
        clearApprovalConsistency();
        throw err;
      }
    } finally {
      if (consistencyRequestRef.current === requestId) setConsistencyChecking(false);
    }
  }

  async function refreshReviewStudioPanels(nextDraft: DraftResponse, preserveSelection = false) {
    const requestId = ++reviewPanelsRequestRef.current;
    const shouldPreserveSelection = preserveSelection && approvalSelectionInitializedRef.current;
    consistencyRequestRef.current += 1;
    setConsistencyChecking(false);
    setReviewPanelsLoading(true);
    setReviewPanelsError('');
    setApprovalPreview(null);
    setApprovalReadiness(null);
    clearApprovalConsistency();
    const version = resolveDraftVersion(nextDraft);
    const knownVersions = [version];
    if (nextDraft.parent_draft_version) knownVersions.push(nextDraft.parent_draft_version);
    setDraftVersions((versions) => Array.from(new Set([...versions, ...knownVersions])).sort((a, b) => a - b));
    setLatestDraftVersion((current) => Math.max(current ?? version, version));
    try {
      const [preview, readiness] = await Promise.all([
        getApprovalPreview(nextDraft.chapter_id),
        getApprovalReadiness(nextDraft.chapter_id),
      ]);
      if (reviewPanelsRequestRef.current !== requestId) return;
      setApprovalPreview(preview);
      setApprovalReadiness(readiness);
      if (!shouldPreserveSelection) initializeApprovalSelection(preview);
      setPreviewConsistency(preview);
      if (nextDraft.parent_draft_version) {
        try {
          const diff = await getDraftDiff(nextDraft.chapter_id, nextDraft.parent_draft_version, nextDraft.draft_version);
          if (reviewPanelsRequestRef.current !== requestId) return;
          setDraftDiff(diff);
        } catch {
          if (reviewPanelsRequestRef.current !== requestId) return;
          setDraftDiff(null);
        }
      } else {
        setDraftDiff(null);
      }
    } catch (err) {
      if (reviewPanelsRequestRef.current !== requestId) return;
      setApprovalPreview(null);
      setApprovalReadiness(null);
      clearApprovalConsistency();
      setReviewPanelsError(err instanceof Error && err.message ? `审批检查加载失败：${err.message}` : '审批检查加载失败，请重试。');
    } finally {
      if (reviewPanelsRequestRef.current === requestId) setReviewPanelsLoading(false);
    }
  }

  async function retryReviewStudioPanels() {
    if (approvalCommitState !== 'idle' || !draft || !isViewingLatestDraft()) return;
    await refreshReviewStudioPanels(draft, true);
  }

  async function handleSuggestGoal() {
    setSuggestingGoal(true);
    setError('');
    try {
      const result = await suggestGoal(localWorld.id);
      setGoal(result.goal);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成章节目标失败');
    } finally {
      setSuggestingGoal(false);
    }
  }

  async function createChapterSession() {
    setWorking(true);
    setError('');
    try {
      const frozenContext = withEditedGoal(executionContext, localWorld, goal);
      const created = await createChapterRequest(localWorld.id, {
        chapter_goal: goal,
        title: goal.slice(0, 40),
        execution_context: frozenContext,
      });
      setChapter(created);
      setOutlineBeats(created.outline_beats);
      setOutlineContext(created.outline_context);
      setDraft(null);
      setApprovalPreview(null);
      clearApprovalSelection();
      clearApprovalConsistency();
      setApprovalReadiness(null);
      setReviewPanelsError('');
      setCritique(null);
      setCharacterArcReport(null);
      setSettlement(null);
      setApprovalCommitState('idle');
      setSettlementSyncError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建章节失败');
    } finally {
      setWorking(false);
    }
  }

  async function autoDraftFirstChapterSession() {
    setWorking(true);
    setAutoDrafting(true);
    setOperationHint('正在生成第一章草稿…');
    setError('');
    try {
      let activeChapter = chapter;
      if (!activeChapter) {
        const frozenContext = withEditedGoal(executionContext, localWorld, goal);
        activeChapter = await createChapterRequest(localWorld.id, {
          chapter_goal: goal,
          title: goal.slice(0, 40),
          execution_context: frozenContext,
        });
        setChapter(activeChapter);
        setOutlineBeats(activeChapter.outline_beats);
        setOutlineContext(activeChapter.outline_context);
        setDraft(null);
        setApprovalPreview(null);
        clearApprovalSelection();
        clearApprovalConsistency();
        setApprovalReadiness(null);
        setCritique(null);
        setCharacterArcReport(null);
        setSettlement(null);
      }

      let activeOutlineBeats = outlineBeats;
      let activeOutlineContext = outlineContext;
      let outlinedChapter = activeChapter;
      if (activeOutlineBeats.length === 0) {
        setOperationHint('正在生成第一章大纲…');
        const outline = await generateOutline(activeChapter.id, { chapter_context: goal });
        activeOutlineBeats = outline.outline_beats;
        activeOutlineContext = outline.outline_context;
        setOutlineBeats(activeOutlineBeats);
        setOutlineContext(activeOutlineContext);
        outlinedChapter = {
          ...activeChapter,
          status: outline.status,
          outline_beats: activeOutlineBeats,
          outline_context: activeOutlineContext,
        };
        setChapter(outlinedChapter);
      }

      setOperationHint('正在生成第一章正文草稿…');
      const nextDraft = normalizeDraft(await writeChapter(activeChapter.id, { outline_beats: activeOutlineBeats }));
      setDraft(nextDraft);
      setDraftVersions([nextDraft.draft_version]);
      setLatestDraftVersion(nextDraft.draft_version);
      await refreshReviewStudioPanels(nextDraft);
      setEditMode(false);
      setEditContent('');
      setChapter({
        ...outlinedChapter,
        title: nextDraft.title,
        status: nextDraft.status ?? 'reviewing',
        outline_beats: nextDraft.outline_beats ?? activeOutlineBeats,
        outline_context: nextDraft.outline_context ?? activeOutlineContext,
        critique_report: nextDraft.critique_report ?? {},
      });
    } catch (err) {
      setError(autoDraftFailureMessage(err));
    } finally {
      setWorking(false);
      setAutoDrafting(false);
      setOperationHint('');
    }
  }

  async function runOutliner() {
    if (approvalCommitState !== 'idle' || !chapter || (draft && !isViewingLatestDraft())) return;
    setWorking(true);
    setOperationHint('编剧室正在排布章节骨架…');
    setError('');
    try {
      const outline = await generateOutline(chapter.id, {});
      setOutlineBeats(outline.outline_beats);
      setOutlineContext(outline.outline_context);
      setChapter({ ...chapter, status: outline.status, outline_beats: outline.outline_beats, outline_context: outline.outline_context });
      setDraft(null);
      setApprovalPreview(null);
      clearApprovalSelection();
      clearApprovalConsistency();
      setApprovalReadiness(null);
      setReviewPanelsError('');
      setCritique(null);
      setCharacterArcReport(null);
      setSettlement(null);
      setApprovalCommitState('idle');
      setSettlementSyncError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成大纲失败');
    } finally {
      setWorking(false);
      setOperationHint('');
    }
  }

  function updateBeat(index: number, patch: Partial<BeatCard>) {
    setOutlineBeats((beats) => beats.map((beat, beatIndex) => (beatIndex === index ? { ...beat, ...patch } : beat)));
  }

  async function runWriter() {
    if (approvalCommitState !== 'idle' || !chapter || (draft && !isViewingLatestDraft())) return;
    setWorking(true);
    setOperationHint('导演正在拆场景…');
    setError('');
    try {
      const nextDraft = normalizeDraft(await writeChapter(chapter.id, { outline_beats: outlineBeats }));
      setDraft(nextDraft);
      setDraftVersions([nextDraft.draft_version]);
      setLatestDraftVersion(nextDraft.draft_version);
      await refreshReviewStudioPanels(nextDraft);
      setCritique(null);
      setCharacterArcReport(null);
      setEditMode(false);
      setEditContent('');
      setChapter({
        ...chapter,
        title: nextDraft.title,
        status: nextDraft.status ?? 'reviewing',
        outline_beats: nextDraft.outline_beats ?? outlineBeats,
        outline_context: nextDraft.outline_context ?? outlineContext,
        critique_report: nextDraft.critique_report ?? {},
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成正文失败');
    } finally {
      setWorking(false);
      setOperationHint('');
    }
  }

  async function runCritic() {
    if (approvalCommitState !== 'idle' || !chapter || !draft || !isViewingLatestDraft()) return;
    setWorking(true);
    setOperationHint('评论席正在检查节奏与设定…');
    setError('');
    try {
      const report = await generateCriticReport(chapter.id);
      setCritique(report);
      setChapter({ ...chapter, critique_report: report });
      await refreshReviewStudioPanels(draft, true);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成 Critic 报告失败');
    } finally {
      setWorking(false);
      setOperationHint('');
    }
  }

  async function runCharacterArcReport() {
    if (approvalCommitState !== 'idle' || !chapter || !draft || !isViewingLatestDraft()) return;
    setWorking(true);
    setError('');
    try {
      setCharacterArcReport(await generateCharacterArcReport(chapter.id));
      await refreshReviewStudioPanels(draft, true);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成角色弧线报告失败');
    } finally {
      setWorking(false);
    }
  }

  function isViewingLatestDraft(): boolean {
    if (!draft) return false;
    return latestDraftVersion === null || resolveDraftVersion(draft) === latestDraftVersion;
  }

  function useHintAsGoal(nextGoal: string) {
    setGoal(nextGoal);
  }

  async function toggleCharacterSelection(changeIndex: number) {
    if (approvalCommitState !== 'idle' || !isViewingLatestDraft()) return;
    const nextCharacterIndexes = toggleIndex(selectedCharacterChangeIndexes, changeIndex);
    setSelectedCharacterChangeIndexes(nextCharacterIndexes);
    try {
      if (!draft) return;
      await refreshApprovalConsistency(draft, nextCharacterIndexes, selectedForeshadowChangeIndexes);
    } catch (err) {
      setError(err instanceof Error ? err.message : '刷新一致性检查失败');
    }
  }

  async function toggleForeshadowSelection(changeIndex: number) {
    if (approvalCommitState !== 'idle' || !isViewingLatestDraft()) return;
    const nextForeshadowIndexes = toggleIndex(selectedForeshadowChangeIndexes, changeIndex);
    setSelectedForeshadowChangeIndexes(nextForeshadowIndexes);
    try {
      if (!draft) return;
      await refreshApprovalConsistency(draft, selectedCharacterChangeIndexes, nextForeshadowIndexes);
    } catch (err) {
      setError(err instanceof Error ? err.message : '刷新一致性检查失败');
    }
  }

  function apiErrorStatus(err: unknown): number | undefined {
    return err instanceof Error && typeof (err as Error & { status?: number }).status === 'number'
      ? (err as Error & { status: number }).status
      : undefined;
  }

  async function loadApprovalSettlement() {
    if (!draft || !approvalPreview) return;
    setWorking(true);
    setOperationHint('正在同步世界推进结算…');
    setSettlementSyncError('');
    try {
      const overview = await apiRequest<WorldOverview>(`/worlds/${localWorld.id}/overview`);
      setLocalWorld(overview);
      setSettlement({
        worldBefore: approvalPreview.world_version_before,
        worldAfter: approvalPreview.world_version_after ?? overview.world_version,
        approvedChapterCount: overview.approved_chapter_count,
        characterChangeCount: selectedCharacterChangeIndexes.length,
        foreshadowChangeCount: selectedForeshadowChangeIndexes.length,
        hasChapterApprovedEvent: overview.recent_events.some((event) => event.event_type === 'chapter_approved' && event.chapter_id === draft.chapter_id),
        overview,
      });
    } catch (err) {
      setSettlementSyncError(err instanceof Error && err.message ? `正史已提交，但世界结算加载失败：${err.message}` : '正史已提交，但世界结算加载失败。');
    } finally {
      setWorking(false);
      setOperationHint('');
    }
  }

  async function reconcileUnknownApproval() {
    if (!draft) return;
    setWorking(true);
    setOperationHint('正在核对正史写入结果…');
    setError('');
    try {
      const history = await getChapterHistoryDetail(draft.chapter_id);
      if (history.approved_version !== resolveDraftVersion(draft)) {
        setError(`服务器显示本章已批准 v${history.approved_version}，与当前草稿 v${resolveDraftVersion(draft)} 不一致。为避免重复写入，本章继续锁定，请返回世界概览核对。`);
        return;
      }
      setApprovalCommitState('committed');
      await loadApprovalSettlement();
    } catch (err) {
      if (apiErrorStatus(err) === 409) {
        setApprovalCommitState('idle');
        setError('服务器确认本章尚未写入正史，已重新加载审批检查，可确认后再次批准。');
        await refreshReviewStudioPanels(draft, true);
      } else {
        setError(err instanceof Error && err.message ? `暂时无法确认正史写入结果：${err.message}` : '暂时无法确认正史写入结果，请重试核对。');
      }
    } finally {
      setWorking(false);
      setOperationHint('');
    }
  }

  async function approveDraft() {
    if (approvalCommitState !== 'idle' || !draft || !approvalPreview || !approvalReadiness || reviewPanelsLoading || reviewPanelsError || consistencyChecking || !consistencyValidated || consistencySummary?.status === 'blocked' || approvalPreview.version_conflict || approvalReadiness.status === 'blocked' || !isViewingLatestDraft()) return;
    setWorking(true);
    setOperationHint('正在写入正史…');
    setError('');
    setSettlementSyncError('');
    try {
      await approveChapter(draft.chapter_id, {
        draft_version: resolveDraftVersion(draft),
        selected_character_change_indexes: selectedCharacterChangeIndexes,
        selected_foreshadow_change_indexes: selectedForeshadowChangeIndexes,
      });
      setApprovalCommitState('committed');
      await loadApprovalSettlement();
    } catch (err) {
      const status = apiErrorStatus(err);
      if (status === undefined || status >= 500) {
        setApprovalCommitState('unknown');
        setError('正史写入请求的结果暂时未知。为避免重复写入，已锁定本章；请先核对写入结果。');
      } else if (status === 409) {
        setApprovalCommitState('idle');
        setApprovalPreview(null);
        setApprovalReadiness(null);
        clearApprovalConsistency();
        setReviewPanelsError('正史写入被服务器拒绝，草稿或世界版本可能已变化。请重新加载审批检查。');
        setError(err instanceof Error ? err.message : '正史写入发生版本冲突');
      } else {
        setApprovalCommitState('idle');
        setError(err instanceof Error ? err.message : '审批草稿失败');
      }
    } finally {
      setWorking(false);
      setOperationHint('');
    }
  }

  async function exportSettlementArchive() {
    if (!settlement) return;
    setWorking(true);
    setError('');
    setSettlement({ ...settlement, exportMessage: undefined, exportError: undefined });
    try {
      const archive = await exportWorldArchiveMarkdown(localWorld.id);
      setSettlement({ ...settlement, exportMessage: `已导出世界档案：${archive.archive_filename}`, exportError: undefined });
    } catch (err) {
      setSettlement({ ...settlement, exportMessage: undefined, exportError: err instanceof Error ? err.message : '导出世界档案失败' });
    } finally {
      setWorking(false);
    }
  }

  function viewSettlementOverview() {
    if (!settlement) return;
    onApproved(settlement.overview);
  }

  function continueNextChapter() {
    if (!settlement) return;
    setLocalWorld(settlement.overview);
    setGoal('');
    setChapter(null);
    setOutlineBeats([]);
    setOutlineContext({});
    setDraft(null);
    setDraftVersions([]);
    setDraftDiff(null);
    setApprovalPreview(null);
    clearApprovalSelection();
    clearApprovalConsistency();
    setApprovalReadiness(null);
    setCritique(null);
    setCharacterArcReport(null);
    setLatestDraftVersion(null);
    setRevisionInstruction('');
    setEditMode(false);
    setEditContent('');
    setSettlement(null);
    setApprovalCommitState('idle');
    setSettlementSyncError('');
  }

  async function rejectDraft() {
    if (approvalCommitState !== 'idle' || !draft || !isViewingLatestDraft()) return;
    const feedback = prompt('请输入驳回反馈（修改建议）：');
    if (!feedback || feedback.trim().length === 0) return;
    setWorking(true);
    setError('');
    try {
      const updated = await rejectDraftRequest(draft.chapter_id, { feedback });
      setDraft(updated);
      if (chapter) setChapter({ ...chapter, status: updated.status ?? 'rejected' });
    } catch (err) {
      setError(err instanceof Error ? err.message : '驳回草稿失败');
    } finally {
      setWorking(false);
    }
  }

  function startEdit() {
    if (approvalCommitState !== 'idle' || !draft || !isViewingLatestDraft()) return;
    setEditMode(true);
    setEditContent(draft.content);
  }

  function cancelEdit() {
    setEditMode(false);
    setEditContent('');
  }

  async function saveEdit() {
    if (approvalCommitState !== 'idle' || !draft || !isViewingLatestDraft()) {
      setError(approvalCommitState !== 'idle' ? '正史写入结果尚未完成同步，当前草稿已锁定。' : '历史版本仅供查看，请切回最新版本后再编辑。');
      setEditMode(false);
      setEditContent('');
      return;
    }
    if (editContent.length < 10) {
      setError('内容至少需要10个字符');
      return;
    }
    setWorking(true);
    setError('');
    try {
      const updated = normalizeDraft(await editDraftRequest(draft.chapter_id, { content: editContent }));
      setDraft(updated);
      await refreshReviewStudioPanels(updated);
      setEditMode(false);
      setEditContent('');
      setCritique(null);
      setCharacterArcReport(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存编辑失败');
    } finally {
      setWorking(false);
    }
  }

  async function saveStash() {
    if (approvalCommitState !== 'idle' || !draft || !isViewingLatestDraft()) return;
    setWorking(true);
    setError('');
    try {
      const updated = normalizeDraft(await stashDraft(draft.chapter_id, { note: '暂存当前草稿' }));
      setDraft(updated);
      await refreshReviewStudioPanels(updated);
      setCritique(null);
      setCharacterArcReport(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '暂存草稿失败');
    } finally {
      setWorking(false);
    }
  }

  async function reviseDraftParagraph(index: number, mode: 'rewrite' | 'polish') {
    if (approvalCommitState !== 'idle' || !draft || !isViewingLatestDraft()) return;
    setWorking(true);
    setError('');
    try {
      const updated = normalizeDraft(await reviseParagraph(draft.chapter_id, { paragraph_index: index, mode }));
      setDraft(updated);
      await refreshReviewStudioPanels(updated);
      setCritique(null);
      setCharacterArcReport(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '段落修订失败');
    } finally {
      setWorking(false);
    }
  }

  async function runFullDraftRevision() {
    if (approvalCommitState !== 'idle' || !draft || !isViewingLatestDraft()) return;
    const instruction = revisionInstruction.trim();
    if (instruction.length < 3) {
      setError('修订指令至少需要3个字符');
      return;
    }
    setWorking(true);
    setError('');
    try {
      const updated = normalizeDraft(await reviseDraft(draft.chapter_id, { instruction }));
      setDraft(updated);
      await refreshReviewStudioPanels(updated);
      setRevisionInstruction('');
      setCritique(null);
      setCharacterArcReport(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成修订版失败');
    } finally {
      setWorking(false);
    }
  }

  async function switchDraftVersion(value: string) {
    if (approvalCommitState !== 'idle' || !draft) return;
    const selected = Number(value);
    if (!Number.isFinite(selected) || selected === resolveDraftVersion(draft)) return;
    setEditMode(false);
    setEditContent('');
    setWorking(true);
    setError('');
    try {
      const selectedDraft = normalizeDraft(await getDraftVersion(draft.chapter_id, selected));
      reviewPanelsRequestRef.current += 1;
      consistencyRequestRef.current += 1;
      setReviewPanelsLoading(false);
      setConsistencyChecking(false);
      setDraft(selectedDraft);
      setApprovalPreview(null);
      clearApprovalSelection();
      clearApprovalConsistency();
      setApprovalReadiness(null);
      setReviewPanelsError('');
      setCritique(null);
      setCharacterArcReport(null);
      if (latestDraftVersion === null || selectedDraft.draft_version === latestDraftVersion) {
        await refreshReviewStudioPanels(selectedDraft);
      } else if (selectedDraft.parent_draft_version) {
        try {
          setDraftDiff(await getDraftDiff(selectedDraft.chapter_id, selectedDraft.parent_draft_version, selectedDraft.draft_version));
        } catch {
          setDraftDiff(null);
        }
      } else {
        try {
          setDraftDiff(await getDraftDiff(selectedDraft.chapter_id, selectedDraft.draft_version, latestDraftVersion));
        } catch {
          setDraftDiff(null);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '切换草稿版本失败');
    } finally {
      setWorking(false);
    }
  }

  const totalPreviewChanges = approvalPreview ? approvalPreview.character_changes.length + approvalPreview.foreshadow_changes.length : 0;
  const selectedPreviewChanges = selectedCharacterChangeIndexes.length + selectedForeshadowChangeIndexes.length;
  const approvalBlockedByConsistency = consistencySummary?.status === 'blocked';
  const approvalBlockedByReview = !approvalPreview || !approvalReadiness || Boolean(reviewPanelsError) || approvalPreview.version_conflict || approvalReadiness.status === 'blocked';
  const approvalResultLocked = approvalCommitState !== 'idle';
  const settlementOnly = Boolean(recentApproval && settlement);

  return (
    <section className="mx-auto max-w-6xl">
      <div className="book-spread grid gap-8 p-6 md:grid-cols-[300px_1fr] md:p-8">
        <aside className="space-y-6 md:border-r md:border-amber-900/15 md:pr-8">
          <button className="ghost-button -ml-4" onClick={onBack}>← 返回世界页</button>
          <div>
            <p className="chapter-kicker">Writing Desk</p>
            <h1 ref={titleRef} tabIndex={-1} className="mt-3 text-3xl font-black text-[#34210f]">创作台</h1>
          </div>
          {!settlementOnly && (
            <div className="book-card p-5">
              <h2 className="font-black text-[#3b2511]">创作流程</h2>
              <ol className="mt-3 space-y-2 text-sm ink-muted">
                <li className={chapter ? 'font-bold text-[#3b2511]' : ''}>1. 创建章节</li>
                <li className={outlineBeats.length ? 'font-bold text-[#3b2511]' : ''}>2. Outliner 大纲</li>
                <li className={draft ? 'font-bold text-[#3b2511]' : ''}>3. Writer 正文</li>
                <li className={critique ? 'font-bold text-[#3b2511]' : ''}>4. Critic 审核</li>
              </ol>
            </div>
          )}
          <div className="book-card p-5">
            <h2 className="font-black text-[#3b2511]">当前上下文</h2>
            <p className="mt-3 ink-muted">世界进度：{localWorld.world_version}</p>
            <p className="mt-2 ink-muted">POV：{localWorld.characters[0]?.name ?? '未设置'}</p>
            <p className="mt-2 ink-muted">故事大纲进度：下一章第 {localWorld.approved_chapter_count + 1} 章</p>
          </div>
          {!settlementOnly && <ExecutionContextSummary context={chapter?.execution_context ?? executionContext} frozen={Boolean(chapter?.execution_context)} />}
          <div className="book-card p-5">
            <h3 className="font-black text-[#3b2511]">紧迫伏笔</h3>
            <div className="mt-3 space-y-2">
              {localWorld.foreshadows.map((item) => <p className="manuscript" key={item.id}>{item.title} · {item.status}</p>)}
            </div>
          </div>
        </aside>
        <div className="space-y-5">
          {!settlementOnly && (
          <div className="book-card p-5">
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm font-bold text-[#5e3b1c]" htmlFor="chapter-goal">章节目标</label>
              <button
                className="inline-flex items-center gap-1.5 rounded-lg border border-amber-700/25 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-900 transition hover:bg-amber-100 disabled:opacity-40"
                disabled={suggestingGoal || Boolean(chapter)}
                onClick={handleSuggestGoal}
                title="AI 根据世界设定、故事大纲、角色和伏笔自动生成章节目标"
              >
                {suggestingGoal ? '⏳ 生成中…' : '✨ 自动生成'}
              </button>
            </div>
            <textarea id="chapter-goal" className="paper-input min-h-28" value={goal} onChange={(event) => setGoal(event.target.value)} aria-label="章节目标" disabled={Boolean(chapter)} placeholder="输入本章要讲什么故事……或者点击「✨ 自动生成」让 AI 帮你写" />
            <div className="mt-4 flex flex-wrap gap-3">
              <button className="primary-button" disabled={working || Boolean(chapter)} onClick={createChapterSession}>{chapter ? '章节已创建' : '创建章节'}</button>
              <button className="secondary-button" disabled={working || approvalResultLocked || !chapter || Boolean(draft && !isViewingLatestDraft())} onClick={runOutliner}>{operationHint === '编剧室正在排布章节骨架…' ? operationHint : '生成大纲'}</button>
              <button className="secondary-button" disabled={working || approvalResultLocked || !chapter || outlineBeats.length === 0 || Boolean(draft && !isViewingLatestDraft())} onClick={runWriter}>{operationHint === '导演正在拆场景…' ? operationHint : '基于大纲生成正文'}</button>
              <button className="secondary-button" disabled={working || approvalResultLocked || !draft || !isViewingLatestDraft()} onClick={runCritic}>{operationHint === '评论席正在检查节奏与设定…' ? operationHint : '生成 Critic 报告'}</button>
              <button className="secondary-button" disabled={working || approvalResultLocked || !draft || !isViewingLatestDraft()} onClick={runCharacterArcReport}>生成角色弧线报告</button>
            </div>
          </div>
          )}

          {error && (
            <div className="paper-error flex flex-wrap items-center justify-between gap-3" role="alert">
              <p>{error}</p>
              {launchContext?.autoDraftFirstChapter && !draft && (
                <button className="secondary-button" disabled={working} onClick={() => void autoDraftFirstChapterSession()}>
                  重试生成第一章草稿
                </button>
              )}
            </div>
          )}

          {approvalCommitState === 'unknown' && (
            <div className="paper-error flex flex-wrap items-center justify-between gap-3" role="alert">
              <p>正史写入结果尚未确认。为避免重复提交，本章编辑与批准已锁定。</p>
              <button className="secondary-button" disabled={working} onClick={() => void reconcileUnknownApproval()}>
                {operationHint === '正在核对正史写入结果…' ? operationHint : '核对正史写入结果'}
              </button>
            </div>
          )}

          {approvalCommitState === 'committed' && settlementSyncError && !settlement && (
            <div className="paper-error flex flex-wrap items-center justify-between gap-3" role="alert">
              <p>{settlementSyncError} 本章不会再次提交写入。</p>
              <button className="secondary-button" disabled={working} onClick={() => void loadApprovalSettlement()}>
                {operationHint === '正在同步世界推进结算…' ? operationHint : '重试加载世界结算'}
              </button>
            </div>
          )}

          {autoDrafting && (
            <p className="paper-success px-4 py-2 text-sm" role="status" aria-live="polite">正在生成第一章草稿，完成后会停在 Studio 审稿，不会写入正史。</p>
          )}

          {launchContext?.autoDraftFirstChapter && draft && !settlement && !autoDrafting && (
            <p className="paper-success px-4 py-2 text-sm" role="status" aria-live="polite">草稿已进入 Studio，确认后再写入正史。</p>
          )}

          {settlement && (
            <section className="book-card space-y-4 border-2 border-emerald-500/35 bg-emerald-50/70 p-5" role="status" aria-live="polite">
              <div>
                <p className="chapter-kicker">正史结算</p>
                <h2 className="text-2xl font-black text-[#203b20]">世界推进结算</h2>
                <p className="manuscript mt-2">这一章已写入正史，后续章节会继承本次世界变化。</p>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <p className="rounded-2xl bg-white/65 p-3 font-bold text-emerald-950">世界进度第 {settlement.worldBefore} 版 → 第 {settlement.worldAfter} 版</p>
                <p className="rounded-2xl bg-white/65 p-3 font-bold text-emerald-950">已写入正史章节：{settlement.approvedChapterCount}</p>
                <p className="rounded-2xl bg-white/65 p-3 font-bold text-emerald-950">角色变化：{settlement.characterChangeCount}</p>
                <p className="rounded-2xl bg-white/65 p-3 font-bold text-emerald-950">悬念/伏笔变化：{settlement.foreshadowChangeCount}</p>
              </div>
              <p className="manuscript text-sm">{settlement.hasChapterApprovedEvent ? '已写入世界历史记录' : '尚未在最近世界历史记录中看到本章事件'}</p>
              <p className="manuscript text-sm">下一章将基于这些变化继续生成。</p>
              {settlement.exportMessage && <p className="paper-success px-4 py-2 text-sm">{settlement.exportMessage}</p>}
              {settlement.exportError && <p className="paper-error">{settlement.exportError}</p>}
              <div className="flex flex-wrap gap-3">
                <button className="primary-button" disabled={working} onClick={continueNextChapter}>继续下一章</button>
                <button className="secondary-button" disabled={working} onClick={viewSettlementOverview}>查看世界概览</button>
                <button className="secondary-button" disabled={working} onClick={() => void exportSettlementArchive()}>导出世界档案</button>
              </div>
            </section>
          )}

          {chapter && (
            <section className="book-card space-y-3 p-5">
              <p className="chapter-kicker">Chapter Session</p>
              <h2 className="text-2xl font-black text-[#34210f]">{chapter.title}</h2>
              <p className="ink-muted">状态：{chapter.status} · 基准世界进度：{chapter.base_world_version}</p>
            </section>
          )}

          {outlineBeats.length > 0 && (
            <section className="book-card space-y-4 p-5">
              <div>
                <p className="chapter-kicker">Outliner Beats</p>
                <h2 className="text-2xl font-black text-[#34210f]">可编辑节拍卡</h2>
                <p className="manuscript mt-2">核心冲突：{String(outlineContext.core_conflict ?? '未提供')}</p>
              </div>
              {outlineBeats.map((beat, index) => (
                <article key={beat.beat_id} className="rounded-2xl border border-amber-900/15 bg-white/35 p-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <label className="block md:col-span-2">
                      <span className="text-sm font-semibold text-[#4a321e]">节拍摘要</span>
                      <textarea className="paper-input mt-1 min-h-20" value={beat.summary} onChange={(event) => updateBeat(index, { summary: event.target.value })} />
                    </label>
                    <label className="block">
                      <span className="text-sm font-semibold text-[#4a321e]">POV</span>
                      <input className="paper-input mt-1" value={beat.pov_character ?? ''} onChange={(event) => updateBeat(index, { pov_character: event.target.value })} />
                    </label>
                    <label className="block">
                      <span className="text-sm font-semibold text-[#4a321e]">地点</span>
                      <input className="paper-input mt-1" value={beat.location ?? ''} onChange={(event) => updateBeat(index, { location: event.target.value })} />
                    </label>
                    <label className="block">
                      <span className="text-sm font-semibold text-[#4a321e]">情绪弧光</span>
                      <input className="paper-input mt-1" value={beat.emotional_arc} onChange={(event) => updateBeat(index, { emotional_arc: event.target.value })} />
                    </label>
                    <label className="block">
                      <span className="text-sm font-semibold text-[#4a321e]">关键对白提示（每行一条）</span>
                      <textarea className="paper-input mt-1 min-h-20" value={dialogueToText(beat)} onChange={(event) => updateBeat(index, { key_dialogue_hints: textToDialogue(event.target.value) })} />
                    </label>
                  </div>
                </article>
              ))}
            </section>
          )}

          {draft && (
            <article className="book-card space-y-5 p-6">
              <div>
                <p className="chapter-kicker">Writer Draft</p>
                <h2 ref={draftTitleRef} tabIndex={-1} className="mt-2 text-3xl font-black text-[#34210f]">{draft.title}</h2>
                <div className="mt-4 flex flex-wrap items-end gap-3">
                  <label className="block">
                    <span className="text-sm font-bold text-[#5e3b1c]">草稿版本</span>
                    <select className="paper-input mt-1" aria-label="草稿版本" value={resolveDraftVersion(draft)} disabled={working || approvalResultLocked || editMode} onChange={(event) => void switchDraftVersion(event.target.value)}>
                      {draftVersions.map((version) => <option key={`draft-version-${version}`} value={version}>v{version}</option>)}
                    </select>
                  </label>
                  <button className="secondary-button" disabled={working || approvalResultLocked || !isViewingLatestDraft()} onClick={saveStash}>暂存当前草稿</button>
                  {draft.change_summary && <p className="manuscript text-sm">最近修改：{draft.change_summary}</p>}
                </div>
              </div>
              <section className="space-y-3 rounded-2xl border border-amber-900/15 bg-amber-50/45 p-4">
                <div>
                  <p className="chapter-kicker">Draft Revision Loop</p>
                  <h3 className="font-black text-[#3b2511]">整稿修订</h3>
                  <p className="manuscript mt-2 text-sm">当前草稿：v{resolveDraftVersion(draft)}</p>
                  {draft.parent_draft_version && <p className="manuscript mt-1 text-sm">父版本：v{draft.parent_draft_version}</p>}
                  <p className="manuscript mt-1 text-sm">修订类型：{draft.change_type}</p>
                </div>
                <label className="block">
                  <span className="text-sm font-semibold text-[#4a321e]">修订指令</span>
                  <textarea
                    className="paper-input mt-1 min-h-24"
                    aria-label="修订指令"
                    value={revisionInstruction}
                    onChange={(event) => setRevisionInstruction(event.target.value)}
                    placeholder="例如：保留雨巷会面，但补足林砚试探沈微霜的过程。"
                    disabled={working || approvalResultLocked || !isViewingLatestDraft()}
                  />
                </label>
                <button className="secondary-button" disabled={working || approvalResultLocked || !isViewingLatestDraft()} onClick={runFullDraftRevision}>生成修订版</button>
                {!isViewingLatestDraft() && <p className="paper-error">正在查看历史版本，切回最新版本后才能批准。</p>}
              </section>
              {draft.rejection_feedback && (
                <div className="rounded-2xl border-2 border-red-400 bg-red-50 p-4">
                  <h3 className="font-black text-red-900">驳回反馈</h3>
                  <p className="manuscript mt-2 text-red-800">{draft.rejection_feedback}</p>
                </div>
              )}
              {editMode ? (
                <div className="space-y-3">
                  <textarea className="paper-input min-h-64" value={editContent} onChange={(event) => setEditContent(event.target.value)} aria-label="编辑草稿内容" />
                  <div className="flex gap-3">
                    <button className="primary-button" disabled={working || approvalResultLocked || !isViewingLatestDraft()} onClick={saveEdit}>保存修改</button>
                    <button className="ghost-button" disabled={working} onClick={cancelEdit}>取消</button>
                  </div>
                </div>
              ) : (
                <p className="manuscript whitespace-pre-wrap text-lg">{draft.content}</p>
              )}
              {!editMode && (
                <section className="space-y-3 rounded-2xl bg-white/35 p-4">
                  <h3 className="font-black text-[#3b2511]">段落级修订</h3>
                  {paragraphList(draft.content).map((paragraph, index) => (
                    <div key={`${index}-${paragraph.slice(0, 24)}`} className="rounded-xl border border-amber-900/10 bg-amber-50/35 p-3">
                      <p className="manuscript whitespace-pre-wrap text-sm leading-relaxed">第 {index + 1} 段：{paragraph}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <button className="secondary-button" disabled={working || approvalResultLocked || !isViewingLatestDraft()} onClick={() => reviseDraftParagraph(index, 'rewrite')}>重写本段</button>
                        <button className="secondary-button" disabled={working || approvalResultLocked || !isViewingLatestDraft()} onClick={() => reviseDraftParagraph(index, 'polish')}>润色本段</button>
                      </div>
                    </div>
                  ))}
                </section>
              )}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl bg-white/35 p-4"><h3 className="font-black text-[#3b2511]">上下文摘要</h3><p className="manuscript mt-2">{draft.context_summary}</p></div>
                <div className="rounded-2xl bg-white/35 p-4"><h3 className="font-black text-[#3b2511]">审核提示</h3>{draft.review_hints.map((hint) => <p key={hint} className="manuscript mt-2">{hint}</p>)}</div>
              </div>
              <ExecutionContextSnapshot context={draft.execution_context ?? chapter?.execution_context} />
              {reviewPanelsError && isViewingLatestDraft() && (
                <div className="paper-error flex flex-wrap items-center justify-between gap-3" role="alert">
                  <p>{reviewPanelsError} 正文、当前版本和审批选择均已保留，重试不会写入正史。</p>
                  <button className="secondary-button" disabled={working || reviewPanelsLoading} onClick={() => void retryReviewStudioPanels()}>
                    {reviewPanelsLoading ? '正在重试审批检查…' : '重试审批检查'}
                  </button>
                </div>
              )}
              {approvalReadiness && <ApprovalReadinessPanel readiness={approvalReadiness} />}
              <section className="space-y-3 rounded-2xl bg-white/35 p-4">
                <h3 className="font-black text-[#3b2511]">版本差异</h3>
                {draftDiff ? (
                  <div className="space-y-1">
                    <p className="manuscript text-sm">v{draftDiff.from_version} → v{draftDiff.to_version}</p>
                    {draftDiff.diff_lines.map((line, index) => (
                      <p
                        key={`${line.type}-${index}`}
                        className={line.type === 'added' ? 'rounded bg-green-100 px-2 py-1 text-green-900' : line.type === 'removed' ? 'rounded bg-red-100 px-2 py-1 text-red-900 line-through' : 'manuscript'}
                      >
                        {line.text}
                      </p>
                    ))}
                  </div>
                ) : (
                  <p className="manuscript text-sm">当前草稿暂无上一版差异。</p>
                )}
              </section>
              {approvalPreview && (
                <section className="space-y-3 rounded-2xl border border-amber-900/15 bg-amber-50/45 p-4">
                  <h3 className="font-black text-[#3b2511]">写入正史前确认</h3>
                  <p className="manuscript">世界进度：{approvalPreview.world_version_before} → {approvalPreview.world_version_after}</p>
                  <p className="manuscript text-sm">已选择 {selectedPreviewChanges} / {totalPreviewChanges} 条拟提交变化</p>
                  {consistencySummary && (
                    <div className="space-y-2 rounded-xl bg-white/45 p-3">
                      <h4 className="font-black text-[#3b2511]">设定冲突检查</h4>
                      <p className="manuscript text-sm"><span>{consistencyLabel(consistencySummary)}</span> · blocking {consistencySummary.blocking_count} / warning {consistencySummary.warning_count} / info {consistencySummary.info_count}</p>
                      {consistencyWarnings.map((warning, index) => (
                        <p
                          key={`${warning.severity}-${warning.category}-${warning.object_id}-${warning.change_index}-${index}`}
                          className={warning.severity === 'blocking' ? 'paper-error' : warning.severity === 'warning' ? 'rounded bg-amber-100 px-3 py-2 text-sm text-amber-900' : 'manuscript text-sm'}
                        >
                          {warning.message}
                        </p>
                      ))}
                    </div>
                  )}
                  {approvalBlockedByConsistency && <p className="paper-error">存在阻塞项，请取消相关变化或重新修订草稿。</p>}
                  {approvalPreview.version_conflict && <p className="paper-error">世界版本已变化，请重新生成草稿。</p>}
                  {approvalPreview.character_changes.map((change, index) => {
                    const changeIndex = previewIndex(change, index);
                    return (
                      <label key={`character-${changeIndex}-${change.character_id}`} className="flex items-start gap-3 rounded-xl bg-white/45 p-3 manuscript text-sm">
                        <input
                          type="checkbox"
                          className="mt-1 accent-amber-800"
                          checked={selectedCharacterChangeIndexes.includes(changeIndex)}
                          disabled={approvalResultLocked || !isViewingLatestDraft()}
                          onChange={() => void toggleCharacterSelection(changeIndex)}
                        />
                        <span>角色：{change.name} · {String(change.before.status ?? '未设置')} → {String(change.after.status ?? '未设置')}</span>
                      </label>
                    );
                  })}
                  {approvalPreview.foreshadow_changes.map((change, index) => {
                    const changeIndex = previewIndex(change, index);
                    return (
                      <label key={`foreshadow-${changeIndex}-${change.foreshadow_id}`} className="flex items-start gap-3 rounded-xl bg-white/45 p-3 manuscript text-sm">
                        <input
                          type="checkbox"
                          className="mt-1 accent-amber-800"
                          checked={selectedForeshadowChangeIndexes.includes(changeIndex)}
                          disabled={approvalResultLocked || !isViewingLatestDraft()}
                          onChange={() => void toggleForeshadowSelection(changeIndex)}
                        />
                        <span>伏笔：{change.title} · {String(change.before.status ?? '未设置')} → {String(change.after.status ?? '未设置')}</span>
                      </label>
                    );
                  })}
                </section>
              )}
              {draft.proposed_changes && (Object.keys(draft.proposed_changes).length > 0) && (
                <div className="space-y-3">
                  <h3 className="font-black text-[#3b2511]">📋 世界状态变化</h3>
                  {/* Character updates */}
                  {Array.isArray((draft.proposed_changes as any).characters) && (draft.proposed_changes as any).characters.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-bold text-[#5e3b1c]">🎭 角色变化</h4>
                      {(draft.proposed_changes as any).characters.map((c: any, i: number) => {
                        const charName = localWorld.characters?.find((ch: any) => ch.id === c.character_id)?.name ?? `角色#${c.character_id}`;
                        return (
                          <div key={i} className="rounded-xl bg-amber-50/60 p-3">
                            <p className="font-bold text-[#3b2511]">{charName} <span className="text-xs font-normal text-amber-700">({c.status})</span></p>
                            {c.current_goals && c.current_goals.length > 0 && (
                              <ul className="mt-1 list-inside list-disc text-sm text-[#4a321e]">
                                {c.current_goals.map((g: string, gi: number) => <li key={gi}>{g}</li>)}
                              </ul>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                  {/* Foreshadow updates */}
                  {Array.isArray((draft.proposed_changes as any).foreshadows) && (draft.proposed_changes as any).foreshadows.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-bold text-[#5e3b1c]">🔮 伏笔推进</h4>
                      {(draft.proposed_changes as any).foreshadows.map((f: any, i: number) => {
                        const fsName = localWorld.foreshadows?.find((fs: any) => fs.id === f.foreshadow_id)?.title ?? `伏笔#${f.foreshadow_id}`;
                        return (
                          <div key={i} className="rounded-xl bg-purple-50/60 p-3">
                            <p className="font-bold text-[#3b2511]">{fsName} <span className="text-xs font-normal text-purple-700">({f.status})</span></p>
                            {f.description_note && <p className="manuscript mt-1 text-sm text-[#4a321e]">{f.description_note}</p>}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </article>
          )}

          {critique && (
            <CriticReportPanel report={critique} working={working || !isViewingLatestDraft()} onReviseParagraph={reviseDraftParagraph} />
          )}

          {characterArcReport && (
            <CharacterArcPanel report={characterArcReport} working={working || !isViewingLatestDraft()} onUseHintAsGoal={isViewingLatestDraft() ? useHintAsGoal : undefined} />
          )}

          {draft && (
            <div className="flex flex-wrap gap-3">
              <button className="primary-button" disabled={working || approvalResultLocked || reviewPanelsLoading || consistencyChecking || !consistencyValidated || !isViewingLatestDraft() || approvalBlockedByConsistency || approvalBlockedByReview} onClick={approveDraft}>{operationHint === '正在写入正史…' ? operationHint : '写入正史并更新世界'}</button>
              <button className="secondary-button" disabled={working || approvalResultLocked || editMode || !isViewingLatestDraft()} onClick={rejectDraft}>驳回</button>
              <button className="secondary-button" disabled={working || approvalResultLocked || editMode || !isViewingLatestDraft()} onClick={startEdit}>编辑正文</button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
