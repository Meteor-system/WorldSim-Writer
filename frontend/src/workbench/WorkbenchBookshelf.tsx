import { useEffect, useState } from 'react';
import { apiRequest, updateWorldStatus } from '../api/client';
import type { WorldOverview, WorldSummary } from '../api/types';
import { worldLoadFailureMessage } from '../world/WorldPageHelpers';

type Props = {
  refreshKey?: { worldId: number; token: number } | null;
  onCreateWorld: () => void;
  onOpenWorld: (world: WorldOverview) => void;
  onWorldRestored?: (world: WorldSummary) => void;
};

const GENRE_LABELS: Record<string, string> = {
  xianxia_intrigue: '仙侠权谋',
  zombie_apocalypse: '丧尸末日',
  mystery_horror: '悬疑惊悚',
  rebirth_revenge: '重生复仇',
  campus_light: '校园轻小说',
};

function labelGenre(genre: string): string {
  return GENRE_LABELS[genre] ?? genre;
}

export function WorkbenchBookshelf({ refreshKey, onCreateWorld, onOpenWorld, onWorldRestored }: Props) {
  const [worlds, setWorlds] = useState<WorldSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [archiveLoading, setArchiveLoading] = useState(false);
  const [openingWorldId, setOpeningWorldId] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError('');
    setLoading(true);
    apiRequest<WorldSummary[]>('/worlds')
      .then((payload) => {
        if (!cancelled) setWorlds(Array.isArray(payload) ? payload : []);
      })
      .catch((err) => {
        if (!cancelled) setError(worldLoadFailureMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey?.token, refreshKey?.worldId]);

  const activeWorlds = worlds.filter((item) => item.status !== 'archived');
  const archivedWorlds = worlds.filter((item) => item.status === 'archived');

  async function openWorld(worldId: number) {
    setOpeningWorldId(worldId);
    setError('');
    try {
      const overview = await apiRequest<WorldOverview>(`/worlds/${worldId}/overview`);
      onOpenWorld(overview);
    } catch (err) {
      setError(err instanceof Error ? err.message : '打开小说失败');
    } finally {
      setOpeningWorldId(null);
    }
  }

  async function restoreWorld(worldId: number) {
    setArchiveLoading(true);
    setError('');
    try {
      const updated = await updateWorldStatus(worldId, { status: 'active' });
      setWorlds((current) => current.map((item) => (item.id === updated.id ? { ...item, status: updated.status } : item)));
      onWorldRestored?.(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : '恢复写作失败');
    } finally {
      setArchiveLoading(false);
    }
  }

  if (loading) {
    return <p className="ink-muted" role="status" aria-live="polite">正在翻找世界手稿…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="chapter-kicker">书架总览</p>
          <h1 className="mt-3 text-4xl font-black text-[#34210f]">作品书架</h1>
          <p className="manuscript mt-3 text-sm text-[#5e3b1c]">打开任意小说进入创作工作台，或新建一个世界开始写作。</p>
        </div>
        <button className="primary-button" type="button" onClick={onCreateWorld}>新建世界</button>
      </div>
      {error && <p className="paper-error mt-5" role="alert">{error}</p>}
      <div className="mt-8 grid gap-5 md:grid-cols-2">
        <section className="book-card p-5">
          <h2 className="text-xl font-black text-[#3b2511]">正在创作</h2>
          <div className="mt-4 space-y-3">
            {activeWorlds.length === 0 && <p className="ink-muted text-sm">暂无活跃小说，点击右上角"新建世界"开始创作。</p>}
            {activeWorlds.map((item) => (
              <article key={item.id} className="rounded-2xl bg-amber-50/60 p-3">
                <p className="font-black text-[#34210f]">{item.title}</p>
                <p className="ink-muted mt-1 text-sm">v{item.world_version} · {labelGenre(item.genre_template)} · 连载中</p>
                <button className="secondary-button mt-3" type="button" disabled={openingWorldId === item.id} onClick={() => void openWorld(item.id)}>
                  {openingWorldId === item.id ? '正在打开…' : `打开 ${item.title}`}
                </button>
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
                <p className="ink-muted mt-1 text-sm">v{item.world_version} · {labelGenre(item.genre_template)} · 已归档</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button className="secondary-button" type="button" disabled={openingWorldId === item.id} onClick={() => void openWorld(item.id)}>打开 {item.title}</button>
                  <button className="primary-button" type="button" disabled={archiveLoading} onClick={() => void restoreWorld(item.id)}>恢复写作 {item.title}</button>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
