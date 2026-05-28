import { useEffect, useRef, useState } from 'react';
import { apiRequest } from '../api/client';
import type { DraftResponse, WorldOverview } from '../api/types';

type Props = { world: WorldOverview; onBack: () => void; onApproved: (world: WorldOverview) => void };

export function StudioPage({ world, onBack, onApproved }: Props) {
  const [goal, setGoal] = useState('推进裂纹玉佩线索，并让林砚发现城主府叛乱传闻的新证据。');
  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState('');
  const titleRef = useRef<HTMLHeadingElement>(null);
  const draftTitleRef = useRef<HTMLHeadingElement>(null);

  async function generateDraft() {
    setWorking(true);
    setError('');
    try {
      setDraft(await apiRequest<DraftResponse>(`/worlds/${world.id}/chapters/draft`, {
        method: 'POST',
        body: JSON.stringify({ chapter_goal: goal }),
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成草稿失败');
    } finally {
      setWorking(false);
    }
  }

  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  useEffect(() => {
    if (draft) draftTitleRef.current?.focus();
  }, [draft]);

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
          <div>
            <label className="mb-2 block text-sm font-bold text-[#5e3b1c]" htmlFor="chapter-goal">章节目标</label>
            <textarea id="chapter-goal" className="paper-input min-h-32" value={goal} onChange={(event) => setGoal(event.target.value)} aria-label="章节目标" />
          </div>
          {error && <p className="paper-error" role="alert">{error}</p>}
          <button className="primary-button" disabled={working} onClick={generateDraft}>{working ? '墨迹未干...' : '生成草稿'}</button>
          {draft && (
            <article className="book-card space-y-5 p-6">
              <div>
                <p className="chapter-kicker">Draft Chapter</p>
                <h2 ref={draftTitleRef} tabIndex={-1} className="mt-2 text-3xl font-black text-[#34210f]">{draft.title}</h2>
              </div>
              <p className="manuscript whitespace-pre-wrap text-lg">{draft.content}</p>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl bg-white/35 p-4"><h3 className="font-black text-[#3b2511]">上下文摘要</h3><p className="manuscript mt-2">{draft.context_summary}</p></div>
                <div className="rounded-2xl bg-white/35 p-4"><h3 className="font-black text-[#3b2511]">审核提示</h3>{draft.review_hints.map((hint) => <p key={hint} className="manuscript mt-2">{hint}</p>)}</div>
              </div>
              <pre className="overflow-auto rounded-2xl border border-amber-900/15 bg-[#2d1d10] p-4 text-sm text-[#f8ead0]">{JSON.stringify(draft.proposed_changes, null, 2)}</pre>
              <button className="primary-button" disabled={working} onClick={approveDraft}>通过并更新世界</button>
            </article>
          )}
        </div>
      </div>
    </section>
  );
}
