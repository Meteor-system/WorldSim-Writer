import { useEffect, useState } from 'react';
import { apiRequest, getConvergenceRatio } from '../api/client';
import type { ConvergenceRatio } from '../api/types';

type ClosureItem = {
  title: string;
  urgency: number;
  window: string | null;
  recommended_chapter: number;
  overdue: boolean;
  priority: string;
};

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
  closure_plan: ClosureItem[];
};

type Props = {
  worldId: number;
  refreshKey?: number;
  chapterGoal?: string;
  totalPlannedChapters?: number;
  onUseGoal?: (goal: string) => void;
};

export function goalFromClosureItem(item: ClosureItem): string {
  return '收束「' + item.title + '」（建议第' + String(item.recommended_chapter) + '章）';
}

export function ConvergencePanel({
  worldId,
  refreshKey = 0,
  chapterGoal = '',
  totalPlannedChapters = 30,
  onUseGoal,
}: Props) {
  const [data, setData] = useState<ConvergenceResponse | null>(null);
  const [ratio, setRatio] = useState<ConvergenceRatio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const planned = Math.min(2000, Math.max(10, totalPlannedChapters));
  const goalOccupied = chapterGoal.trim().length > 0;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    Promise.all([
      apiRequest<ConvergenceResponse>('/worlds/' + worldId + '/convergence?total_planned_chapters=' + String(planned)),
      getConvergenceRatio(worldId).catch(() => null),
    ])
      .then(([payload, ratioPayload]) => {
        if (cancelled) return;
        setData(typeof payload === 'object' && payload !== null && 'entropy' in payload ? payload : null);
        setRatio(ratioPayload && typeof ratioPayload.ratio === 'number' ? ratioPayload : null);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : '收束面板加载失败');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [worldId, refreshKey, planned]);

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
      {ratio && (
        <p className="manuscript text-sm">收束比 {ratio.ratio} · 新开 {ratio.opened_threads} / 关闭 {ratio.closed_threads}</p>
      )}
      <div>
        <h4 className="text-sm font-bold text-[#5e3b1c]">开放线索</h4>
        {data.open_threads.length === 0 && <p className="manuscript text-sm">没有开放线索。</p>}
        <ul className="mt-1 space-y-1">
          {data.open_threads.map((thread) => (
            <li key={thread.title} className="manuscript text-sm">
              <span className={thread.classification === 'must_resolve' ? 'font-bold text-red-800' : ''}>{thread.title}</span>
              {' · '}{thread.classification}{thread.window ? ' · ' + thread.window : ''}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h4 className="text-sm font-bold text-[#5e3b1c]">收束计划</h4>
        {data.closure_plan.length === 0 && <p className="manuscript text-sm">暂无待收束的伏笔。</p>}
        <ul className="mt-1 space-y-2">
          {data.closure_plan.map((item) => (
            <li key={item.title} className="manuscript text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className={item.overdue ? 'font-bold text-red-800' : ''}>{item.priority} {item.title} → 建议第{item.recommended_chapter}章{item.overdue ? '（已逾期）' : ''}</span>
                {onUseGoal && (
                  <button
                    type="button"
                    className="secondary-button"
                    disabled={goalOccupied}
                    onClick={() => onUseGoal(goalFromClosureItem(item))}
                  >
                    用作本章目标
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
        {onUseGoal && goalOccupied && <p className="ink-muted mt-2 text-xs">章节目标非空，未覆盖。</p>}
      </div>
    </section>
  );
}
