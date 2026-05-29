import { useEffect, useRef, useState } from 'react';
import { apiRequest, createWorld, generateStoryArc } from '../api/client';
import type { StoryArcChapter, WorldCreateRequest, WorldOverview } from '../api/types';
import { CharacterManager } from '../components/CharacterManager';
import { ForeshadowManager } from '../components/ForeshadowManager';
import { WorldCreationForm } from './WorldCreationForm';

type Props = { onEnterStudio: (world: WorldOverview) => void; autoFocusTitle?: boolean };

type Tab = 'overview' | 'characters' | 'foreshadows';

const TABS: { key: Tab; label: string }[] = [
  { key: 'overview', label: '世界概览' },
  { key: 'characters', label: '角色管理' },
  { key: 'foreshadows', label: '伏笔账本' },
];

function describeEvent(event: { event_type: string; payload: Record<string, unknown> }, world: WorldOverview): string {
  const payload = event.payload as Record<string, any>;
  const chapterTitle = payload.chapter_title
    ? `《${payload.chapter_title}》`
    : payload.chapter_id
      ? `第${payload.chapter_id}章`
      : '';

  switch (event.event_type) {
    case 'chapter_approved':
      return `✅ ${chapterTitle} 通过审核，正式纳入故事`;
    case 'character_change': {
      const char = world.current_characters?.find((c) => c.id === payload.object_id);
      const charName = char?.name ?? payload.object_id ?? '某角色';
      const change = payload.change as string;
      if (change === 'created') return `🎭 新角色「${charName}」登场`;
      if (change === 'updated') {
        const after = payload.after as Record<string, any>;
        const before = payload.before as Record<string, any>;
        if (after?.current_goals && before?.current_goals) {
          return `🎭 ${charName} 的目标更新为：${after.current_goals.join('、')}`;
        }
        return `🎭 ${charName} 的状态发生了变化`;
      }
      return `🎭 ${charName} 发生了变化`;
    }
    case 'foreshadow_change': {
      const fs = world.current_foreshadows?.find((f) => f.id === payload.object_id);
      const fsName = fs?.title ?? payload.object_id ?? '某伏笔';
      const change = payload.change as string;
      if (change === 'created') return `🔮 埋下伏笔「${fsName}」`;
      if (change === 'updated') {
        const after = payload.after as Record<string, any>;
        if (after?.status) {
          const statusMap: Record<string, string> = {
            planted: '已埋下', advanced: '推进中', partially_resolved: '部分揭晓',
            fully_resolved: '已揭晓', abandoned: '已废弃',
          };
          return `🔮 伏笔「${fsName}」${statusMap[after.status] ?? after.status}`;
        }
        return `🔮 伏笔「${fsName}」发生了变化`;
      }
      return `🔮 伏笔「${fsName}」发生了变化`;
    }
    case 'world_version_increment':
      return `📖 世界版本更新至 v${payload.world_version_after ?? event.event_type}`;
    default:
      return `${event.event_type}`;
  }
}

function StoryArcCard({ chapter }: { chapter: StoryArcChapter }) {
  return (
    <article className="rounded-2xl border border-amber-900/15 bg-white/35 p-4">
      <p className="chapter-kicker">第 {chapter.chapter_number} 章</p>
      <h3 className="mt-2 text-xl font-black text-[#34210f]">{chapter.title}</h3>
      <p className="manuscript mt-3">{chapter.summary}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl bg-amber-50/60 p-3">
          <p className="text-sm font-bold text-[#5e3b1c]">核心冲突</p>
          <p className="manuscript mt-1">{chapter.core_conflict}</p>
        </div>
        <div className="rounded-2xl bg-amber-50/60 p-3">
          <p className="text-sm font-bold text-[#5e3b1c]">POV 建议</p>
          <p className="manuscript mt-1">{chapter.pov_suggestion}</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {chapter.foreshadow_hints.length === 0 && <span className="ink-muted text-sm">无指定伏笔</span>}
        {chapter.foreshadow_hints.map((hint) => (
          <span key={hint} className="rounded-full border border-amber-900/15 bg-amber-100/70 px-3 py-1 text-xs font-bold text-[#5e3b1c]">
            {hint}
          </span>
        ))}
      </div>
    </article>
  );
}

export function WorldPage({ onEnterStudio, autoFocusTitle = true }: Props) {
  const [world, setWorld] = useState<WorldOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [arcLoading, setArcLoading] = useState(false);
  const [tab, setTab] = useState<Tab>('overview');
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

  async function submitWorld(payload: WorldCreateRequest) {
    setCreating(true);
    setError('');
    try {
      const created = await createWorld(payload);
      setWorld(await apiRequest<WorldOverview>(`/worlds/${created.id}/overview`));
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建世界失败');
    } finally {
      setCreating(false);
    }
  }

  async function runStoryArcPlanner() {
    if (!world) return;
    setArcLoading(true);
    setError('');
    try {
      const response = await generateStoryArc(world.id);
      setWorld({ ...world, story_arc: response.story_arc });
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成故事大纲失败');
    } finally {
      setArcLoading(false);
    }
  }

  useEffect(() => {
    void loadWorld();
  }, []);

  useEffect(() => {
    if (!loading && autoFocusTitle) titleRef.current?.focus();
  }, [autoFocusTitle, loading, world?.id]);

  if (loading)
    return (
      <p className="p-8 ink-muted" role="status" aria-live="polite">
        正在翻找世界手稿...
      </p>
    );

  if (!world) {
    return (
      <section>
        {error && (
          <div className="mx-auto mt-8 max-w-5xl px-6">
            <p className="paper-error text-left" role="alert">
              {error}
            </p>
          </div>
        )}
        <WorldCreationForm creating={creating} onCreate={submitWorld} />
      </section>
    );
  }

  return (
    <section className="px-6 py-8 md:px-10">
      <div className="book-spread p-8 md:p-10">
        {/* Tab bar */}
        <nav className="mb-8 flex flex-wrap gap-1 rounded-full border border-amber-900/15 bg-amber-50/50 p-1">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex-1 rounded-full px-4 py-2 text-sm font-bold transition-colors ${
                tab === t.key
                  ? 'bg-amber-900 text-amber-50 shadow-sm'
                  : 'text-amber-900/70 hover:bg-amber-100'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>

        {/* Tab content */}
        {tab === 'overview' && (
          <div className="grid gap-8 md:grid-cols-[1fr_1fr]">
            <div>
              <p className="chapter-kicker">World Canon</p>
              <h1
                ref={titleRef}
                tabIndex={-1}
                className="mt-3 text-4xl font-black text-[#34210f]"
              >
                {world.title}
              </h1>
              <p className="mt-3 ink-muted">
                第 {world.world_version} 版 · {world.genre_template} · {world.status}
              </p>
              <p className="manuscript mt-8 text-lg">{world.truth_canon}</p>
              {error && (
                <p className="paper-error mt-5" role="alert">
                  {error}
                </p>
              )}
              <div className="mt-8 flex flex-wrap gap-3">
                <button className="primary-button" onClick={() => onEnterStudio(world)}>
                  进入创作台
                </button>
                <button className="secondary-button" disabled={arcLoading} onClick={runStoryArcPlanner}>
                  {arcLoading ? '规划中...' : world.story_arc.length ? '重新生成故事大纲' : '生成故事大纲'}
                </button>
              </div>
            </div>
            <div className="space-y-4">
              <article className="book-card p-5">
                <h2 className="text-lg font-black text-[#3b2511]">角色线索</h2>
                <div className="mt-3 space-y-3">
                  {world.characters.map((character) => (
                    <p className="manuscript" key={character.id}>
                      {character.name}：{character.current_goals.join('、')}
                    </p>
                  ))}
                </div>
              </article>
              <article className="book-card p-5">
                <h2 className="text-lg font-black text-[#3b2511]">伏笔笺</h2>
                <div className="mt-3 space-y-3">
                  {world.foreshadows.map((item) => (
                    <p className="manuscript" key={item.id}>
                      {item.title}：{item.status}
                    </p>
                  ))}
                </div>
              </article>
              <article className="book-card p-5">
                <h2 className="text-lg font-black text-[#3b2511]">最近事件</h2>
                <div className="mt-3 space-y-2 ink-muted">
                  {world.recent_events.length === 0 && <p>还没有正式写入的章节事件。</p>}
                  {world.recent_events.map((event) => (
                    <p key={event.id} className="manuscript">
                      {describeEvent(event, world)}
                    </p>
                  ))}
                </div>
              </article>
            </div>
            <section className="book-card p-5 md:col-span-2">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="chapter-kicker">Story Arc Planner</p>
                  <h2 className="mt-2 text-2xl font-black text-[#34210f]">前 10 章故事弧线</h2>
                </div>
                <p className="ink-muted text-sm">下一章目标会按已批准章节数自动带入创作台。</p>
              </div>
              {world.story_arc.length === 0 ? (
                <p className="manuscript mt-4">还没有故事弧线。生成后会自动为创作台填入下一章目标。</p>
              ) : (
                <div className="mt-5 grid gap-4">
                  {world.story_arc.map((chapter) => (
                    <StoryArcCard key={chapter.chapter_number} chapter={chapter} />
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        {tab === 'characters' && <CharacterManager worldId={world.id} onChanged={loadWorld} />}

        {tab === 'foreshadows' && (
          <ForeshadowManager worldId={world.id} characters={world.characters} onChanged={loadWorld} />
        )}
      </div>
    </section>
  );
}
