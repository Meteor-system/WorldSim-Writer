import { useEffect, useState } from 'react';
import { retrieveWorldMemory } from '../api/client';
import type { MemoryRetrieveResponse } from '../api/types';

type Props = { worldId: number; chapterGoal: string; refreshKey?: number };

export function MemoryRetrievePanel({ worldId, chapterGoal, refreshKey = 0 }: Props) {
  const [data, setData] = useState<MemoryRetrieveResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    retrieveWorldMemory(worldId, chapterGoal)
      .then((payload) => {
        if (!cancelled && payload && Array.isArray(payload.retrieved)) setData(payload);
        else if (!cancelled) setData(null);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : '记忆检索失败');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [worldId, chapterGoal, refreshKey]);

  if (loading && !data) return <p className="manuscript text-sm">记忆检索中…</p>;
  if (error && !data) return <p className="paper-error">{error}</p>;
  if (!data) return <p className="manuscript text-sm">还没有可检索的世界记忆。</p>;

  return (
    <section className="space-y-3 rounded-2xl border border-amber-900/15 bg-amber-50/45 p-4" aria-label="下一章记忆检索">
      <h3 className="font-black text-[#3b2511]">下一章将注入的记忆</h3>
      <p className="manuscript text-sm">查询：{data.query || '当前世界状态'}</p>
      {data.retrieved.length === 0 && <p className="manuscript text-sm">没有匹配的记忆摘要。</p>}
      <ul className="space-y-2">
        {data.retrieved.map((item) => (
          <li key={String(item.chapter_start) + '-' + String(item.chapter_end)} className="rounded-xl bg-white/45 p-3 manuscript text-sm">
            <p className="font-bold">第{item.chapter_start}-{item.chapter_end}章</p>
            <p className="mt-1">{item.summary}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
