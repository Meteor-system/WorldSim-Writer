import { useEffect, useRef, useState } from 'react';
import {
  apiRequest,
  createChapter as createChapterRequest,
  critiqueChapter,
  generateOutline,
  writeChapter,
} from '../api/client';
import type { BeatCard, ChapterPipelineResponse, CritiqueReport, DraftResponse, WorldOverview } from '../api/types';

type Props = { world: WorldOverview; onBack: () => void; onApproved: (world: WorldOverview) => void };

function dialogueToText(beat: BeatCard): string {
  return beat.key_dialogue_hints.join('\n');
}

function textToDialogue(value: string): string[] {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

export function StudioPage({ world, onBack, onApproved }: Props) {
  const [goal, setGoal] = useState('推进裂纹玉佩线索，并让林砚发现城主府叛乱传闻的新证据。');
  const [chapter, setChapter] = useState<ChapterPipelineResponse | null>(null);
  const [outlineBeats, setOutlineBeats] = useState<BeatCard[]>([]);
  const [outlineContext, setOutlineContext] = useState<Record<string, unknown>>({});
  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [critique, setCritique] = useState<CritiqueReport | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const titleRef = useRef<HTMLHeadingElement>(null);
  const draftTitleRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  useEffect(() => {
    if (draft) draftTitleRef.current?.focus();
  }, [draft]);

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
      const nextDraft = await writeChapter(chapter.id, { outline_beats: outlineBeats });
      setDraft(nextDraft);
      setCritique(null);
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
      const response = await critiqueChapter(chapter.id);
      setCritique(response.critique_report);
      setChapter({ ...chapter, status: response.status, critique_report: response.critique_report });
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成审核报告失败');
    } finally {
      setWorking(false);
    }
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
      const updated = await apiRequest<DraftResponse>(`/chapters/${draft.chapter_id}/draft`, {
        method: 'PUT',
        body: JSON.stringify({ content: editContent }),
      });
      setDraft(updated);
      setEditMode(false);
      setEditContent('');
      setCritique(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存编辑失败');
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
            <label className="mb-2 block text-sm font-bold text-[#5e3b1c]" htmlFor="chapter-goal">章节目标</label>
            <textarea id="chapter-goal" className="paper-input min-h-28" value={goal} onChange={(event) => setGoal(event.target.value)} aria-label="章节目标" disabled={Boolean(chapter)} />
            <div className="mt-4 flex flex-wrap gap-3">
              <button className="primary-button" disabled={working || Boolean(chapter)} onClick={createChapterSession}>{chapter ? '章节已创建' : '创建章节'}</button>
              <button className="secondary-button" disabled={working || !chapter} onClick={runOutliner}>生成大纲</button>
              <button className="secondary-button" disabled={working || !chapter || outlineBeats.length === 0} onClick={runWriter}>基于大纲生成正文</button>
              <button className="secondary-button" disabled={working || !draft} onClick={runCritic}>生成 Critic 报告</button>
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
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl bg-white/35 p-4"><h3 className="font-black text-[#3b2511]">上下文摘要</h3><p className="manuscript mt-2">{draft.context_summary}</p></div>
                <div className="rounded-2xl bg-white/35 p-4"><h3 className="font-black text-[#3b2511]">审核提示</h3>{draft.review_hints.map((hint) => <p key={hint} className="manuscript mt-2">{hint}</p>)}</div>
              </div>
              <pre className="overflow-auto rounded-2xl border border-amber-900/15 bg-[#2d1d10] p-4 text-sm text-[#f8ead0]">{JSON.stringify(draft.proposed_changes, null, 2)}</pre>
            </article>
          )}

          {critique && (
            <section className="book-card space-y-4 p-5">
              <div>
                <p className="chapter-kicker">Critic Report</p>
                <h2 className="text-2xl font-black text-[#34210f]">评分：{critique.score}/100</h2>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl bg-white/35 p-4">
                  <h3 className="font-black text-[#3b2511]">问题列表</h3>
                  {critique.issues.map((issue, index) => (
                    <p key={`${issue.category}-${index}`} className="manuscript mt-2">[{issue.severity}] {issue.category}：{issue.message}</p>
                  ))}
                </div>
                <div className="rounded-2xl bg-white/35 p-4">
                  <h3 className="font-black text-[#3b2511]">修改建议</h3>
                  {critique.suggestions.map((suggestion) => <p key={suggestion} className="manuscript mt-2">{suggestion}</p>)}
                </div>
              </div>
              <pre className="overflow-auto rounded-2xl border border-amber-900/15 bg-[#2d1d10] p-4 text-sm text-[#f8ead0]">{JSON.stringify(critique.consistency_check, null, 2)}</pre>
            </section>
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
