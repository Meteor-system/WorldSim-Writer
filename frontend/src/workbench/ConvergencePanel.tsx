import { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';

type ConvergenceResponse = {
  world_id: number;
  chapter_number: number;
  total_planned_chapters: number;
  arc_mode: string;
  arc_mode_label: string;
  entropy: number;
  entropy_level: string;
  entropy_message: string;
  entropy_breakdown: Record<string, number>;
  open_threads: { title: string; kind: string; urgency: number; window: string | null; classification: string }[];
  closure_plan: { title: string; urgency: number; window: string | null; recommended_chapter: number; overdue: boolean; priority: string }[];
};

type Props = {
  worldId: number;
  refreshKey?: number;
};

export function ConvergencePanel({ worldId, refreshKey = 0 }: Props) {
  const [data, setData] = useState<ConvergenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    apiRequest<ConvergenceResponse>(`/worlds/${worldId}/convergence?total_planned_chapters=200`)
      .then((payload) => {
        if (!cancelled) setData(typeof payload === 'object' && payload !== null && 'entropy' in payload ? payload : null);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : '收束面板加载失败');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [worldId, refreshKey]);

  if (loading && !data) return <p className="manuscript text-sm">收束面板加载中…</p>;
  if (error && !data) return <p className="paper-error">{error}</p>;
  if (!data || typeof data.entropy !== 'number' || typeof data.arc_mode !== 'string') return null;

  return (
    <section className="space-y-3 rounded-2xl border border-amber-900/15 bg-amber-50/45 p-4" aria-label="叙事收束面板">
      <h3 className="font-black text-[#3b2511]">叙事收束</h3>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="rounded-xl bg-white/45 p-3">
          <p className="ink-muted">叙事熵</p>
          <p className="font-black text-lg text-[#3b2511]">{data.entropy}</p>
          <p className="text-xs">{data.entropy_message}</p>
        </div>
        <div className="rounded-xl bg-white/45 p-3">
          <p className="ink-muted">篇章模式</p>
          <p className="font-black text-[#3b2511]">{data.arc_mode}</p>
          <p className="text-xs">{data.arc_mode_label}</p>
        </div>
      </div>
      <div>
        <h4 className="text-sm font-bold text-[#5e3b1c]">开放线索</h4>
        {data.open_threads.length === 0 && <p className="manuscript text-sm">没有开放线索。</p>}
        <ul className="mt-1 space-y-1">
          {data.open_threads.map((thread) => (
            <li key={thread.title} className="manuscript text-sm">
              <span className={thread.classification === 'must_resolve' ? 'font-bold text-red-800' : ''}>{thread.title}</span>
              {' · '}{thread.classification}{thread.window ? ` · ${thread.window}` : ''}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h4 className="text-sm font-bold text-[#5e3b1c]">收束计划</h4>
        {data.closure_plan.length === 0 && <p className="manuscript text-sm">暂无待收束的伏笔。</p>}
        <ul className="mt-1 space-y-1">
          {data.closure_plan.map((item) => (
            <li key={item.title} className="manuscript text-sm">
              <span className={item.overdue ? 'font-bold text-red-800' : ''}>{item.priority} {item.title}</span>
              {' → 建议第'}{item.recommended_chapter}章{item.overdue ? '（已逾期）' : ''}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
