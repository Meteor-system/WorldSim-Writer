import { useEffect, useRef, useState } from 'react';
import {
  apiRequest,
  approveChapter,
  checkApprovalConsistency,
  createChapter as createChapterRequest,
  generateCharacterArcReport,
  generateCriticReport,
  generateOutline,
  getApprovalPreview,
  getApprovalReadiness,
  getDraftDiff,
  getDraftVersion,
  exportWorldArchiveMarkdown,
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
  materialReferenceTitles: string[];
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

function materialReferenceTitles(context?: ChapterExecutionContext | null): string[] {
  return (context?.material_references ?? []).map((reference) => reference.title).filter(Boolean);
}

function materialReferenceSentence(titles: string[]): string {
  if (titles.length === 0) return '本章未使用导入素材参考。';
  return `本章参考了 ${titles.length} 条导入素材：${titles.join('、')}。`;
}

function MaterialReferenceCards({ context, compact = false }: { context?: ChapterExecutionContext | null; compact?: boolean }) {
  const references = context?.material_references ?? [];
  if (references.length === 0) return null;
  return (
    <div className={compact ? 'mt-3 space-y-2' : 'mt-3 rounded-2xl bg-white/45 p-3'}>
      {!compact && <p className="text-sm font-bold text-[#4a321e]">导入素材参考：{references.length} 条</p>}
      {references.map((reference) => (
        <article key={`${reference.source_title}-${reference.title}`} className="rounded-xl border border-amber-900/10 bg-amber-50/35 p-3">
          <p className="manuscript text-sm font-bold text-[#5e3b1c]">{reference.title}（来源：{reference.source_title}）</p>
          <p className="manuscript mt-1 text-sm text-[#5e3b1c]">{reference.summary}</p>
        </article>
      ))}
      <p className="manuscript text-sm font-bold text-[#5e3b1c]">{compact ? '素材参考不会自动改写正式设定。' : '导入素材只是本章写作参考，不会自动改写正式设定。'}</p>
    </div>
  );
}

function ExecutionContextSummary({ context, frozen }: { context?: ChapterExecutionContext | null; frozen?: boolean }) {
  if (!context) {
    return (
      <div className="book-card p-5">
        <h2 className="font-black text-[#3b2511]">本章执行上下文</h2>
        <p className="mt-3 ink-muted">本章暂无 NCC 执行上下文。创建章节时会根据当前目标生成手动上下文快照。</p>
      </div>
    );
  }
  return (
    <div className="book-card p-5">
      <h2 className="font-black text-[#3b2511]">本章执行上下文</h2>
      {frozen && <p className="mt-2 text-sm font-bold text-[#5e3b1c]">已冻结执行上下文：{context.source} · v{context.source_world_version}</p>}
      <p className="mt-3 ink-muted">来源：{sourceLabel(context.source)}</p>
      <p className="mt-2 ink-muted">源世界版本：v{context.source_world_version}</p>
      <p className="mt-2 ink-muted">建议章节：第 {context.next_chapter_number ?? '?'} 章</p>
      <p className="mt-2 ink-muted">推荐 POV：{context.recommended_pov.name ?? '暂无'}</p>
      <p className="mt-2 ink-muted">优先角色：{names(context.priority_characters)}</p>
      <p className="mt-2 ink-muted">优先伏笔：{names(context.priority_foreshadows)}</p>
      <p className="mt-2 ink-muted">推进提示：{context.progression_hints.length} 条</p>
      <p className="mt-2 ink-muted">连续性提醒：{context.continuity_warnings.length} 条</p>
      <MaterialReferenceCards context={context} />
    </div>
  );
}

function ExecutionContextSnapshot({ context }: { context?: ChapterExecutionContext | null }) {
  if (!context) return null;
  return (
    <section className="space-y-3 rounded-2xl bg-white/35 p-4">
      <h3 className="font-black text-[#3b2511]">执行上下文快照</h3>
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
      <MaterialReferenceCards context={context} compact />
    </section>
  );
}

export function StudioPage({ world, launchContext, onBack, onApproved }: Props) {
  const [localWorld, setLocalWorld] = useState(world);
  const [goal, setGoal] = useState(launchContext?.initialChapterGoal ?? '');
  const [executionContext] = useState(launchContext?.executionContext);
  const [chapter, setChapter] = useState<ChapterPipelineResponse | null>(null);
  const [outlineBeats, setOutlineBeats] = useState<BeatCard[]>([]);
  const [outlineContext, setOutlineContext] = useState<Record<string, unknown>>({});
  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [draftVersions, setDraftVersions] = useState<number[]>([]);
  const [draftDiff, setDraftDiff] = useState<DraftDiffResponse | null>(null);
  const [approvalPreview, setApprovalPreview] = useState<ApprovalPreviewResponse | null>(null);
  const [selectedCharacterChangeIndexes, setSelectedCharacterChangeIndexes] = useState<number[]>([]);
  const [selectedForeshadowChangeIndexes, setSelectedForeshadowChangeIndexes] = useState<number[]>([]);
  const [consistencySummary, setConsistencySummary] = useState<ConsistencySummary | null>(null);
  const [consistencyWarnings, setConsistencyWarnings] = useState<ConsistencyWarning[]>([]);
  const [approvalReadiness, setApprovalReadiness] = useState<ApprovalReadinessResponse | null>(null);
  const [critique, setCritique] = useState<CriticReportResponse | null>(null);
  const [characterArcReport, setCharacterArcReport] = useState<CharacterArcReportResponse | null>(null);
  const [settlement, setSettlement] = useState<WorldSettlement | null>(null);
  const [latestDraftVersion, setLatestDraftVersion] = useState<number | null>(null);
  const [revisionInstruction, setRevisionInstruction] = useState('');
  const [working, setWorking] = useState(false);
  const [operationHint, setOperationHint] = useState('');
  const [suggestingGoal, setSuggestingGoal] = useState(false);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const titleRef = useRef<HTMLHeadingElement>(null);
  const draftTitleRef = useRef<HTMLHeadingElement>(null);

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
  }

  function clearApprovalSelection() {
    setSelectedCharacterChangeIndexes([]);
    setSelectedForeshadowChangeIndexes([]);
  }

  function clearApprovalConsistency() {
    setConsistencySummary(null);
    setConsistencyWarnings([]);
  }

  function setPreviewConsistency(preview: ApprovalPreviewResponse) {
    setConsistencySummary(preview.consistency_summary);
    setConsistencyWarnings(preview.consistency_warnings);
  }

  function consistencyLabel(summary: ConsistencySummary): string {
    if (summary.status === 'blocked') return '存在阻塞项';
    if (summary.status === 'needs_review') return '存在需复核项';
    return '一致性检查通过';
  }

  async function refreshApprovalConsistency(characterIndexes: number[], foreshadowIndexes: number[]) {
    if (!draft) return;
    const result = await checkApprovalConsistency(draft.chapter_id, {
      draft_version: resolveDraftVersion(draft),
      selected_character_change_indexes: characterIndexes,
      selected_foreshadow_change_indexes: foreshadowIndexes,
    });
    setConsistencySummary(result.consistency_summary);
    setConsistencyWarnings(result.consistency_warnings);
  }

  async function refreshReviewStudioPanels(nextDraft: DraftResponse) {
    const version = resolveDraftVersion(nextDraft);
    const knownVersions = [version];
    if (nextDraft.parent_draft_version) knownVersions.push(nextDraft.parent_draft_version);
    setDraftVersions((versions) => Array.from(new Set([...versions, ...knownVersions])).sort((a, b) => a - b));
    setLatestDraftVersion((current) => Math.max(current ?? version, version));
    try {
      const preview = await getApprovalPreview(nextDraft.chapter_id);
      setApprovalPreview(preview);
      initializeApprovalSelection(preview);
      setPreviewConsistency(preview);
    } catch {
      setApprovalPreview(null);
      clearApprovalSelection();
      clearApprovalConsistency();
    }
    try {
      setApprovalReadiness(await getApprovalReadiness(nextDraft.chapter_id));
    } catch {
      setApprovalReadiness(null);
    }
    if (nextDraft.parent_draft_version) {
      try {
        setDraftDiff(await getDraftDiff(nextDraft.chapter_id, nextDraft.parent_draft_version, nextDraft.draft_version));
      } catch {
        setDraftDiff(null);
      }
    } else {
      setDraftDiff(null);
    }
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
      setCritique(null);
      setCharacterArcReport(null);
      setSettlement(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建章节失败');
    } finally {
      setWorking(false);
    }
  }

  async function runOutliner() {
    if (!chapter) return;
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
      setCritique(null);
      setCharacterArcReport(null);
      setSettlement(null);
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
    if (!chapter) return;
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
    if (!chapter || !draft) return;
    setWorking(true);
    setOperationHint('评论席正在检查节奏与设定…');
    setError('');
    try {
      const report = await generateCriticReport(chapter.id);
      setCritique(report);
      setChapter({ ...chapter, critique_report: report });
      try {
        setApprovalReadiness(await getApprovalReadiness(chapter.id));
      } catch {
        setApprovalReadiness(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成 Critic 报告失败');
    } finally {
      setWorking(false);
      setOperationHint('');
    }
  }

  async function runCharacterArcReport() {
    if (!chapter || !draft) return;
    setWorking(true);
    setError('');
    try {
      setCharacterArcReport(await generateCharacterArcReport(chapter.id));
      try {
        setApprovalReadiness(await getApprovalReadiness(chapter.id));
      } catch {
        setApprovalReadiness(null);
      }
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
    const nextCharacterIndexes = toggleIndex(selectedCharacterChangeIndexes, changeIndex);
    setSelectedCharacterChangeIndexes(nextCharacterIndexes);
    try {
      await refreshApprovalConsistency(nextCharacterIndexes, selectedForeshadowChangeIndexes);
    } catch (err) {
      setError(err instanceof Error ? err.message : '刷新一致性检查失败');
    }
  }

  async function toggleForeshadowSelection(changeIndex: number) {
    const nextForeshadowIndexes = toggleIndex(selectedForeshadowChangeIndexes, changeIndex);
    setSelectedForeshadowChangeIndexes(nextForeshadowIndexes);
    try {
      await refreshApprovalConsistency(selectedCharacterChangeIndexes, nextForeshadowIndexes);
    } catch (err) {
      setError(err instanceof Error ? err.message : '刷新一致性检查失败');
    }
  }

  async function approveDraft() {
    if (!draft) return;
    setWorking(true);
    setOperationHint('正在写入正史…');
    setError('');
    try {
      const settledMaterialReferenceTitles = materialReferenceTitles(draft.execution_context ?? chapter?.execution_context ?? executionContext);
      await approveChapter(draft.chapter_id, {
        draft_version: resolveDraftVersion(draft),
        selected_character_change_indexes: selectedCharacterChangeIndexes,
        selected_foreshadow_change_indexes: selectedForeshadowChangeIndexes,
      });
      const overview = await apiRequest<WorldOverview>(`/worlds/${localWorld.id}/overview`);
      setLocalWorld(overview);
      setSettlement({
        worldBefore: approvalPreview?.world_version_before ?? localWorld.world_version,
        worldAfter: approvalPreview?.world_version_after ?? overview.world_version,
        approvedChapterCount: overview.approved_chapter_count,
        characterChangeCount: selectedCharacterChangeIndexes.length,
        foreshadowChangeCount: selectedForeshadowChangeIndexes.length,
        hasChapterApprovedEvent: overview.recent_events.some((event) => event.event_type === 'chapter_approved'),
        materialReferenceTitles: settledMaterialReferenceTitles,
        overview,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '审批草稿失败');
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
  }

  async function rejectDraft() {
    if (!draft) return;
    const feedback = prompt('请输入驳回反馈（修改建议）：');
    if (!feedback || feedback.trim().length === 0) return;
    setWorking(true);
    setError('');
    try {
      const updated = await apiRequest<DraftResponse>(`/chapters/${draft.chapter_id}/reject`, {
        method: 'POST',
        body: JSON.stringify({ feedback }),
      });
      setDraft(updated);
      if (chapter) setChapter({ ...chapter, status: updated.status ?? 'rejected' });
    } catch (err) {
      setError(err instanceof Error ? err.message : '驳回草稿失败');
    } finally {
      setWorking(false);
    }
  }

  function startEdit() {
    if (!draft) return;
    setEditMode(true);
    setEditContent(draft.content);
  }

  function cancelEdit() {
    setEditMode(false);
    setEditContent('');
  }

  async function saveEdit() {
    if (!draft || editContent.length < 10) {
      setError('内容至少需要10个字符');
      return;
    }
    setWorking(true);
    setError('');
    try {
      const updated = normalizeDraft(await apiRequest<DraftResponse>(`/chapters/${draft.chapter_id}/draft`, {
        method: 'PUT',
        body: JSON.stringify({ content: editContent }),
      }));
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
    if (!draft) return;
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
    if (!draft) return;
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
    if (!draft) return;
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
    if (!draft) return;
    const selected = Number(value);
    if (!Number.isFinite(selected) || selected === resolveDraftVersion(draft)) return;
    setWorking(true);
    setError('');
    try {
      const selectedDraft = normalizeDraft(await getDraftVersion(draft.chapter_id, selected));
      setDraft(selectedDraft);
      if (selectedDraft.parent_draft_version) {
        try {
          setDraftDiff(await getDraftDiff(selectedDraft.chapter_id, selectedDraft.parent_draft_version, selectedDraft.draft_version));
        } catch {
          setDraftDiff(null);
        }
      } else if (latestDraftVersion && selectedDraft.draft_version !== latestDraftVersion) {
        try {
          setDraftDiff(await getDraftDiff(selectedDraft.chapter_id, selectedDraft.draft_version, latestDraftVersion));
        } catch {
          setDraftDiff(null);
        }
      } else {
        setDraftDiff(null);
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

  return (
    <section className="mx-auto max-w-6xl">
      <div className="book-spread grid gap-8 p-6 md:grid-cols-[300px_1fr] md:p-8">
        <aside className="space-y-6 md:border-r md:border-amber-900/15 md:pr-8">
          <button className="ghost-button -ml-4" onClick={onBack}>← 返回世界页</button>
          <div>
            <p className="chapter-kicker">Writing Desk</p>
            <h1 ref={titleRef} tabIndex={-1} className="mt-3 text-3xl font-black text-[#34210f]">创作台</h1>
          </div>
          <div className="book-card p-5">
            <h2 className="font-black text-[#3b2511]">创作流程</h2>
            <ol className="mt-3 space-y-2 text-sm ink-muted">
              <li className={chapter ? 'font-bold text-[#3b2511]' : ''}>1. 创建章节</li>
              <li className={outlineBeats.length ? 'font-bold text-[#3b2511]' : ''}>2. Outliner 大纲</li>
              <li className={draft ? 'font-bold text-[#3b2511]' : ''}>3. Writer 正文</li>
              <li className={critique ? 'font-bold text-[#3b2511]' : ''}>4. Critic 审核</li>
            </ol>
          </div>
          <div className="book-card p-5">
            <h2 className="font-black text-[#3b2511]">当前上下文</h2>
            <p className="mt-3 ink-muted">世界进度：{localWorld.world_version}</p>
            <p className="mt-2 ink-muted">POV：{localWorld.characters[0]?.name ?? '未设置'}</p>
            <p className="mt-2 ink-muted">故事大纲进度：下一章第 {localWorld.approved_chapter_count + 1} 章</p>
          </div>
          <ExecutionContextSummary context={chapter?.execution_context ?? executionContext} frozen={Boolean(chapter?.execution_context)} />
          <div className="book-card p-5">
            <h3 className="font-black text-[#3b2511]">紧迫伏笔</h3>
            <div className="mt-3 space-y-2">
              {localWorld.foreshadows.map((item) => <p className="manuscript" key={item.id}>{item.title} · {item.status}</p>)}
            </div>
          </div>
        </aside>
        <div className="space-y-5">
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
              <button className="secondary-button" disabled={working || !chapter} onClick={runOutliner}>{operationHint === '编剧室正在排布章节骨架…' ? operationHint : '生成大纲'}</button>
              <button className="secondary-button" disabled={working || !chapter || outlineBeats.length === 0} onClick={runWriter}>{operationHint === '导演正在拆场景…' ? operationHint : '基于大纲生成正文'}</button>
              <button className="secondary-button" disabled={working || !draft} onClick={runCritic}>{operationHint === '评论席正在检查节奏与设定…' ? operationHint : '生成 Critic 报告'}</button>
              <button className="secondary-button" disabled={working || !draft} onClick={runCharacterArcReport}>生成角色弧线报告</button>
            </div>
          </div>

          {error && <p className="paper-error" role="alert">{error}</p>}

          {settlement && (
            <section className="book-card space-y-4 border-2 border-emerald-500/35 bg-emerald-50/70 p-5" role="status" aria-live="polite">
              <div>
                <p className="chapter-kicker">Canon Settlement</p>
                <h2 className="text-2xl font-black text-[#203b20]">世界推进结算</h2>
                <p className="manuscript mt-2">这一章已写入正式设定，后续章节会继承本次世界变化。</p>
              </div>
              <div className="rounded-2xl bg-white/65 p-4 text-emerald-950">
                <p className="font-bold">{materialReferenceSentence(settlement.materialReferenceTitles)}</p>
                {settlement.materialReferenceTitles.length > 0 && (
                  <p className="manuscript mt-2 text-sm">导入素材仍是本章创作参考，没有自动写入正式设定。</p>
                )}
                <p className="manuscript mt-2 text-sm">已写入正式章节。</p>
                <p className="manuscript mt-1 text-sm">
                  {settlement.hasChapterApprovedEvent ? '正式事件：章节已批准并写入世界历史。' : '正式事件：正在等待世界历史刷新。'}
                </p>
                <p className="manuscript mt-1 text-sm">世界版本：第 {settlement.worldBefore} 版 → 第 {settlement.worldAfter} 版。</p>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <p className="rounded-2xl bg-white/65 p-3 font-bold text-emerald-950">世界进度 v{settlement.worldBefore} → v{settlement.worldAfter}</p>
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
                    <select className="paper-input mt-1" aria-label="草稿版本" value={resolveDraftVersion(draft)} onChange={(event) => void switchDraftVersion(event.target.value)}>
                      {draftVersions.map((version) => <option key={`draft-version-${version}`} value={version}>v{version}</option>)}
                    </select>
                  </label>
                  <button className="secondary-button" disabled={working || !isViewingLatestDraft()} onClick={saveStash}>暂存当前草稿</button>
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
                    disabled={working || !isViewingLatestDraft()}
                  />
                </label>
                <button className="secondary-button" disabled={working || !isViewingLatestDraft()} onClick={runFullDraftRevision}>生成修订版</button>
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
                    <button className="primary-button" disabled={working} onClick={saveEdit}>保存修改</button>
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
                        <button className="secondary-button" disabled={working || !isViewingLatestDraft()} onClick={() => reviseDraftParagraph(index, 'rewrite')}>重写本段</button>
                        <button className="secondary-button" disabled={working || !isViewingLatestDraft()} onClick={() => reviseDraftParagraph(index, 'polish')}>润色本段</button>
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
            <CriticReportPanel report={critique} working={working} onReviseParagraph={reviseDraftParagraph} />
          )}

          {characterArcReport && (
            <CharacterArcPanel report={characterArcReport} working={working} onUseHintAsGoal={useHintAsGoal} />
          )}

          {draft && (
            <div className="flex flex-wrap gap-3">
              <button className="primary-button" disabled={working || !isViewingLatestDraft() || approvalBlockedByConsistency} onClick={approveDraft}>{operationHint === '正在写入正史…' ? operationHint : '写入正史并更新世界'}</button>
              <button className="secondary-button" disabled={working || editMode || !isViewingLatestDraft()} onClick={rejectDraft}>驳回</button>
              <button className="secondary-button" disabled={working || editMode || !isViewingLatestDraft()} onClick={startEdit}>编辑正文</button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
