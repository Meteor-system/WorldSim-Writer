import { useEffect, useRef, useState } from 'react';
import {
  apiRequest,
  createChapter as createChapterRequest,
  generateCharacterArcReport,
  generateCriticReport,
  generateOutline,
  getApprovalPreview,
  getDraftDiff,
  reviseParagraph,
  stashDraft,
  suggestGoal,
  writeChapter,
} from '../api/client';
import type { ApprovalPreviewResponse, BeatCard, ChapterPipelineResponse, CharacterArcReportResponse, CriticReportResponse, DraftDiffResponse, DraftResponse, WorldOverview } from '../api/types';
import { CharacterArcPanel } from './CharacterArcPanel';
import { CriticReportPanel } from './CriticReportPanel';

type Props = { world: WorldOverview; initialChapterGoal?: string; onBack: () => void; onApproved: (world: WorldOverview) => void };

function dialogueToText(beat: BeatCard): string {
  return beat.key_dialogue_hints.join('\n');
}

function textToDialogue(value: string): string[] {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

export function StudioPage({ world, initialChapterGoal, onBack, onApproved }: Props) {
  const [goal, setGoal] = useState(initialChapterGoal ?? '');
  const [chapter, setChapter] = useState<ChapterPipelineResponse | null>(null);
  const [outlineBeats, setOutlineBeats] = useState<BeatCard[]>([]);
  const [outlineContext, setOutlineContext] = useState<Record<string, unknown>>({});
  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [draftVersions, setDraftVersions] = useState<number[]>([]);
  const [draftDiff, setDraftDiff] = useState<DraftDiffResponse | null>(null);
  const [approvalPreview, setApprovalPreview] = useState<ApprovalPreviewResponse | null>(null);
  const [critique, setCritique] = useState<CriticReportResponse | null>(null);
  const [characterArcReport, setCharacterArcReport] = useState<CharacterArcReportResponse | null>(null);
  const [working, setWorking] = useState(false);
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
    if (initialChapterGoal || chapter || goal.trim().length > 0) return;
    const nextChapterNumber = world.approved_chapter_count + 1;
    const nextArcChapter = world.story_arc.find((item) => item.chapter_number === nextChapterNumber);
    if (nextArcChapter) setGoal(nextArcChapter.summary);
  }, [chapter, goal, initialChapterGoal, world.approved_chapter_count, world.story_arc]);

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

  async function refreshReviewStudioPanels(nextDraft: DraftResponse) {
    const version = resolveDraftVersion(nextDraft);
    setDraftVersions((versions) => Array.from(new Set([...versions, version])).sort((a, b) => a - b));
    try {
      const preview = await getApprovalPreview(nextDraft.chapter_id);
      setApprovalPreview(preview);
    } catch {
      setApprovalPreview(null);
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
      const result = await suggestGoal(world.id);
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
      const created = await createChapterRequest(world.id, { chapter_goal: goal, title: goal.slice(0, 40) });
      setChapter(created);
      setOutlineBeats(created.outline_beats);
      setOutlineContext(created.outline_context);
      setDraft(null);
      setCritique(null);
      setCharacterArcReport(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建章节失败');
    } finally {
      setWorking(false);
    }
  }

  async function runOutliner() {
    if (!chapter) return;
    setWorking(true);
    setError('');
    try {
      const outline = await generateOutline(chapter.id, {});
      setOutlineBeats(outline.outline_beats);
      setOutlineContext(outline.outline_context);
      setChapter({ ...chapter, status: outline.status, outline_beats: outline.outline_beats, outline_context: outline.outline_context });
      setDraft(null);
      setCritique(null);
      setCharacterArcReport(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成大纲失败');
    } finally {
      setWorking(false);
    }
  }

  function updateBeat(index: number, patch: Partial<BeatCard>) {
    setOutlineBeats((beats) => beats.map((beat, beatIndex) => (beatIndex === index ? { ...beat, ...patch } : beat)));
  }

  async function runWriter() {
    if (!chapter) return;
    setWorking(true);
    setError('');
    try {
      const nextDraft = normalizeDraft(await writeChapter(chapter.id, { outline_beats: outlineBeats }));
      setDraft(nextDraft);
      setDraftVersions([nextDraft.draft_version]);
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
    }
  }

  async function runCritic() {
    if (!chapter || !draft) return;
    setWorking(true);
    setError('');
    try {
      const report = await generateCriticReport(chapter.id);
      setCritique(report);
      setChapter({ ...chapter, critique_report: report });
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成 Critic 报告失败');
    } finally {
      setWorking(false);
    }
  }

  async function runCharacterArcReport() {
    if (!chapter || !draft) return;
    setWorking(true);
    setError('');
    try {
      setCharacterArcReport(await generateCharacterArcReport(chapter.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成角色弧线报告失败');
    } finally {
      setWorking(false);
    }
  }

  function useHintAsGoal(nextGoal: string) {
    setGoal(nextGoal);
  }

  async function approveDraft() {
    if (!draft) return;
    setWorking(true);
    setError('');
    try {
      await apiRequest(`/chapters/${draft.chapter_id}/approve`, { method: 'POST', body: '{}' });
      onApproved(await apiRequest<WorldOverview>(`/worlds/${world.id}/overview`));
    } catch (err) {
      setError(err instanceof Error ? err.message : '审批草稿失败');
    } finally {
      setWorking(false);
    }
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
            <h2 className="font-black text-[#3b2511]">Pipeline</h2>
            <ol className="mt-3 space-y-2 text-sm ink-muted">
              <li className={chapter ? 'font-bold text-[#3b2511]' : ''}>1. 创建章节</li>
              <li className={outlineBeats.length ? 'font-bold text-[#3b2511]' : ''}>2. Outliner 大纲</li>
              <li className={draft ? 'font-bold text-[#3b2511]' : ''}>3. Writer 正文</li>
              <li className={critique ? 'font-bold text-[#3b2511]' : ''}>4. Critic 审核</li>
            </ol>
          </div>
          <div className="book-card p-5">
            <h2 className="font-black text-[#3b2511]">当前上下文</h2>
            <p className="mt-3 ink-muted">世界版本：{world.world_version}</p>
            <p className="mt-2 ink-muted">POV：{world.characters[0]?.name ?? '未设置'}</p>
            <p className="mt-2 ink-muted">故事大纲进度：下一章第 {world.approved_chapter_count + 1} 章</p>
          </div>
          <div className="book-card p-5">
            <h3 className="font-black text-[#3b2511]">紧迫伏笔</h3>
            <div className="mt-3 space-y-2">
              {world.foreshadows.map((item) => <p className="manuscript" key={item.id}>{item.title} · {item.status}</p>)}
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
              <button className="secondary-button" disabled={working || !chapter} onClick={runOutliner}>生成大纲</button>
              <button className="secondary-button" disabled={working || !chapter || outlineBeats.length === 0} onClick={runWriter}>基于大纲生成正文</button>
              <button className="secondary-button" disabled={working || !draft} onClick={runCritic}>生成 Critic 报告</button>
              <button className="secondary-button" disabled={working || !draft} onClick={runCharacterArcReport}>生成角色弧线报告</button>
            </div>
          </div>

          {error && <p className="paper-error" role="alert">{error}</p>}

          {chapter && (
            <section className="book-card space-y-3 p-5">
              <p className="chapter-kicker">Chapter Session</p>
              <h2 className="text-2xl font-black text-[#34210f]">{chapter.title}</h2>
              <p className="ink-muted">状态：{chapter.status} · 基准世界版本：{chapter.base_world_version}</p>
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
                    <select className="paper-input mt-1" aria-label="草稿版本" value={resolveDraftVersion(draft)} onChange={() => undefined}>
                      {draftVersions.map((version) => <option key={`draft-version-${version}`} value={version}>v{version}</option>)}
                    </select>
                  </label>
                  <button className="secondary-button" disabled={working} onClick={saveStash}>暂存当前草稿</button>
                  {draft.change_summary && <p className="manuscript text-sm">最近修改：{draft.change_summary}</p>}
                </div>
              </div>
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
                        <button className="secondary-button" disabled={working} onClick={() => reviseDraftParagraph(index, 'rewrite')}>重写本段</button>
                        <button className="secondary-button" disabled={working} onClick={() => reviseDraftParagraph(index, 'polish')}>润色本段</button>
                      </div>
                    </div>
                  ))}
                </section>
              )}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl bg-white/35 p-4"><h3 className="font-black text-[#3b2511]">上下文摘要</h3><p className="manuscript mt-2">{draft.context_summary}</p></div>
                <div className="rounded-2xl bg-white/35 p-4"><h3 className="font-black text-[#3b2511]">审核提示</h3>{draft.review_hints.map((hint) => <p key={hint} className="manuscript mt-2">{hint}</p>)}</div>
              </div>
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
                  <h3 className="font-black text-[#3b2511]">通过后将提交</h3>
                  <p className="manuscript">世界版本：{approvalPreview.world_version_before} → {approvalPreview.world_version_after}</p>
                  {approvalPreview.version_conflict && <p className="paper-error">世界版本已变化，请重新生成草稿。</p>}
                  {approvalPreview.character_changes.map((change) => (
                    <p key={`character-${change.character_id}`} className="manuscript text-sm">角色：{change.name} · {String(change.before.status ?? '未设置')} → {String(change.after.status ?? '未设置')}</p>
                  ))}
                  {approvalPreview.foreshadow_changes.map((change) => (
                    <p key={`foreshadow-${change.foreshadow_id}`} className="manuscript text-sm">伏笔：{change.title} · {String(change.before.status ?? '未设置')} → {String(change.after.status ?? '未设置')}</p>
                  ))}
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
                        const charName = world.characters?.find((ch: any) => ch.id === c.character_id)?.name ?? `角色#${c.character_id}`;
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
                        const fsName = world.foreshadows?.find((fs: any) => fs.id === f.foreshadow_id)?.title ?? `伏笔#${f.foreshadow_id}`;
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
              <button className="primary-button" disabled={working} onClick={approveDraft}>通过并更新世界</button>
              <button className="secondary-button" disabled={working || editMode} onClick={rejectDraft}>驳回</button>
              <button className="secondary-button" disabled={working || editMode} onClick={startEdit}>编辑正文</button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
