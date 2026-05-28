import { useEffect, useRef, useState } from 'react';
import { apiRequest } from '../api/client';
import type { WorldOverview } from '../api/types';

type Props = { onEnterStudio: (world: WorldOverview) => void; autoFocusTitle?: boolean };

export function WorldPage({ onEnterStudio, autoFocusTitle = true }: Props) {
  const [world, setWorld] = useState<WorldOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const titleRef = useRef<HTMLHeadingElement>(null);

  async function loadWorld() {
    setError('');
    try {
      const worlds = await apiRequest<Array<{ id: number }>>('/worlds');
      if (worlds.length === 0) {
        setWorld(null);
      } else {
        setWorld(await apiRequest<WorldOverview>(`/worlds/${worlds[0].id}/overview`));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载世界失败');
    } finally {
      setLoading(false);
    }
  }

  async function createWorld() {
    setLoading(true);
    setError('');
    try {
      const created = await apiRequest<{ id: number }>('/worlds/from-template', { method: 'POST', body: '{}' });
      setWorld(await apiRequest<WorldOverview>(`/worlds/${created.id}/overview`));
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建世界失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadWorld();
  }, []);

  useEffect(() => {
    if (!loading && autoFocusTitle) titleRef.current?.focus();
  }, [autoFocusTitle, loading, world?.id]);

  if (loading) return <p className="p-8 ink-muted" role="status" aria-live="polite">正在翻找世界手稿...</p>;

  if (!world) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-12 text-center">
        <p className="chapter-kicker">Empty Manuscript</p>
        <h1 ref={titleRef} tabIndex={-1} className="mt-3 text-4xl font-black text-[#34210f]">还没有世界</h1>
        <p className="manuscript mx-auto mt-4 max-w-xl">创建内置示例世界，让“青岚城风云”成为这本书的第一页。</p>
        {error && <p className="paper-error mt-5 text-left" role="alert">{error}</p>}
        <button className="primary-button mt-8" onClick={createWorld}>创建“青岚城风云”</button>
      </section>
    );
  }

  return (
    <section className="px-6 py-8 md:px-10">
      <div className="book-spread p-8 md:p-10">
        <div className="grid gap-8 md:grid-cols-[1fr_1fr]">
          <div>
            <p className="chapter-kicker">World Canon</p>
            <h1 ref={titleRef} tabIndex={-1} className="mt-3 text-4xl font-black text-[#34210f]">{world.title}</h1>
            <p className="mt-3 ink-muted">第 {world.world_version} 版 · {world.genre_template} · {world.status}</p>
            <p className="manuscript mt-8 text-lg">{world.truth_canon}</p>
            {error && <p className="paper-error mt-5" role="alert">{error}</p>}
            <button className="primary-button mt-8" onClick={() => onEnterStudio(world)}>进入创作台</button>
          </div>
          <div className="space-y-4">
            <article className="book-card p-5">
              <h2 className="text-lg font-black text-[#3b2511]">角色线索</h2>
              <div className="mt-3 space-y-3">
                {world.characters.map((character) => <p className="manuscript" key={character.id}>{character.name}：{character.current_goals.join('、')}</p>)}
              </div>
            </article>
            <article className="book-card p-5">
              <h2 className="text-lg font-black text-[#3b2511]">伏笔笺</h2>
              <div className="mt-3 space-y-3">
                {world.foreshadows.map((item) => <p className="manuscript" key={item.id}>{item.title}：{item.status}</p>)}
              </div>
            </article>
            <article className="book-card p-5">
              <h2 className="text-lg font-black text-[#3b2511]">最近事件</h2>
              <div className="mt-3 space-y-2 ink-muted">
                {world.recent_events.length === 0 && <p>还没有正式写入的章节事件。</p>}
                {world.recent_events.map((event) => <p key={event.id}>{event.event_type}: {event.world_version_before} → {event.world_version_after}</p>)}
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>
  );
}
