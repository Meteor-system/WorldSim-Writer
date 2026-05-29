import { useCallback, useEffect, useState } from 'react';
import {
  createForeshadow,
  deleteForeshadow,
  getForeshadowTimeline,
  getForeshadows,
  getStaleForeshadows,
  updateForeshadow,
} from '../api/client';
import type {
  Character,
  Foreshadow,
  ForeshadowCreate,
  ForeshadowEvent,
  ForeshadowStatus,
  ForeshadowUpdate,
  StaleForeshadow,
} from '../api/types';

type Props = { worldId: number; characters: Character[]; onChanged?: () => Promise<void> | void };

const TYPE_OPTIONS = ['plot', 'character', 'world', 'theme'] as const;
const TYPE_LABELS: Record<string, string> = {
  plot: '情节',
  character: '角色',
  world: '世界',
  theme: '主题',
};

const STATUS_OPTIONS = ['planted', 'advanced', 'resolved', 'expired'] as const satisfies readonly ForeshadowStatus[];
const STATUS_LABELS: Record<ForeshadowStatus, string> = {
  planted: '已埋设',
  advanced: '已推进',
  resolved: '已收束',
  expired: '已过期',
};

const STATUS_COLORS: Record<ForeshadowStatus, string> = {
  planted: 'bg-emerald-100 text-emerald-800 border-emerald-700/20',
  advanced: 'bg-amber-100 text-amber-800 border-amber-700/20',
  resolved: 'bg-stone-200 text-stone-700 border-stone-500/20',
  expired: 'bg-red-100 text-red-800 border-red-700/20',
};

const URGENCY_LABELS: Record<number, string> = {
  1: '极低',
  2: '低',
  3: '中',
  4: '高',
  5: '极高',
};

type FormData = {
  title: string;
  description: string;
  foreshadow_type: string;
  status: ForeshadowStatus;
  urgency_level: number;
  related_character_ids: number[];
  expected_resolution_window: string;
};

const EMPTY_FORM: FormData = {
  title: '',
  description: '',
  foreshadow_type: 'plot',
  status: 'planted',
  urgency_level: 3,
  related_character_ids: [],
  expected_resolution_window: '',
};

function formFromForeshadow(f: Foreshadow): FormData {
  return {
    title: f.title,
    description: f.description,
    foreshadow_type: f.foreshadow_type,
    status: f.status,
    urgency_level: f.urgency_level,
    related_character_ids: [...f.related_character_ids],
    expected_resolution_window: f.expected_resolution_window ?? '',
  };
}

function formToPayload(f: FormData): ForeshadowCreate {
  return {
    title: f.title.trim(),
    description: f.description.trim(),
    foreshadow_type: f.foreshadow_type,
    status: f.status,
    urgency_level: f.urgency_level,
    related_character_ids: f.related_character_ids,
    expected_resolution_window: f.expected_resolution_window.trim() || undefined,
  };
}

function nextForwardStatus(statusValue: ForeshadowStatus): ForeshadowStatus | null {
  if (statusValue === 'planted') return 'advanced';
  if (statusValue === 'advanced') return 'resolved';
  return null;
}

export function ForeshadowManager({ worldId, characters, onChanged }: Props) {
  const [foreshadows, setForeshadows] = useState<Foreshadow[]>([]);
  const [staleForeshadows, setStaleForeshadows] = useState<StaleForeshadow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormData>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [draggingId, setDraggingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [foreshadowItems, staleItems] = await Promise.all([
        getForeshadows(worldId),
        getStaleForeshadows(worldId),
      ]);
      setForeshadows(foreshadowItems);
      setStaleForeshadows(staleItems);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载伏笔失败');
    } finally {
      setLoading(false);
    }
  }, [worldId]);

  useEffect(() => {
    void load();
  }, [load]);

  function openCreate() {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setShowForm(true);
  }

  function openEdit(f: Foreshadow) {
    setForm(formFromForeshadow(f));
    setEditingId(f.id);
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title.trim() || !form.description.trim()) return;
    setSubmitting(true);
    setError('');
    try {
      if (editingId) {
        const payload: ForeshadowUpdate = formToPayload(form);
        await updateForeshadow(editingId, payload);
      } else {
        await createForeshadow(worldId, formToPayload(form));
      }
      closeForm();
      await load();
      await onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存伏笔失败');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    setError('');
    try {
      await deleteForeshadow(id);
      setConfirmDelete(null);
      await load();
      await onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除伏笔失败');
    }
  }

  async function advanceStatus(f: Foreshadow) {
    const next = nextForwardStatus(f.status);
    if (!next) return;
    try {
      await updateForeshadow(f.id, { status: next });
      await load();
      await onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新伏笔状态失败');
    }
  }

  async function dropOnStatus(statusValue: ForeshadowStatus) {
    if (draggingId === null) return;
    const source = foreshadows.find((item) => item.id === draggingId);
    setDraggingId(null);
    if (!source || source.status === statusValue) return;
    try {
      await updateForeshadow(source.id, { status: statusValue });
      await load();
      await onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新伏笔状态失败');
    }
  }

  function toggleRelatedCharacter(characterId: number) {
    setForm((current) => ({
      ...current,
      related_character_ids: current.related_character_ids.includes(characterId)
        ? current.related_character_ids.filter((id) => id !== characterId)
        : [...current.related_character_ids, characterId],
    }));
  }

  function charName(id: number) {
    return characters.find((c) => c.id === id)?.name ?? `#${id}`;
  }

  function renderForeshadowCard(f: Foreshadow) {
    const next = nextForwardStatus(f.status);
    return (
      <article
        key={f.id}
        draggable
        onDragStart={() => setDraggingId(f.id)}
        onDragEnd={() => setDraggingId(null)}
        className="book-card p-5 flex flex-col gap-3"
      >
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-lg font-black text-[#3b2511] leading-snug">{f.title}</h3>
          <button
            className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-70 ${STATUS_COLORS[f.status]}`}
            onClick={() => void advanceStatus(f)}
            disabled={next === null}
            title={next ? '推进到下一状态' : '终态不可继续推进'}
          >
            {STATUS_LABELS[f.status]}
          </button>
        </div>

        <p className="manuscript text-sm leading-relaxed">{f.description}</p>

        <div className="flex flex-wrap gap-2 text-xs ink-muted">
          <span className="rounded-full border border-amber-800/20 px-2 py-0.5">
            类型：{TYPE_LABELS[f.foreshadow_type] ?? f.foreshadow_type}
          </span>
          <span className="rounded-full border border-amber-800/20 px-2 py-0.5">
            紧迫度：{URGENCY_LABELS[f.urgency_level] ?? f.urgency_level}
          </span>
          {f.expected_resolution_window && (
            <span className="rounded-full border border-amber-800/20 px-2 py-0.5">
              窗口：{f.expected_resolution_window}
            </span>
          )}
        </div>

        {f.related_character_ids.length > 0 && (
          <p className="text-xs ink-muted">
            <span className="font-semibold">关联角色：</span>
            {f.related_character_ids.map(charName).join('、')}
          </p>
        )}

        <button className="ghost-button text-sm self-start" onClick={() => setExpandedId(expandedId === f.id ? null : f.id)}>
          {expandedId === f.id ? '收起时间线' : '展开时间线'}
        </button>
        {expandedId === f.id && <ForeshadowTimeline foreshadowId={f.id} />}

        <div className="mt-auto flex gap-2 pt-2">
          <button className="secondary-button text-sm" onClick={() => openEdit(f)}>
            编辑
          </button>
          {confirmDelete === f.id ? (
            <>
              <button
                className="rounded-full border border-red-800/40 bg-red-100 px-3 py-1.5 text-sm font-bold text-red-800"
                onClick={() => handleDelete(f.id)}
              >
                确认删除
              </button>
              <button className="ghost-button text-sm" onClick={() => setConfirmDelete(null)}>
                取消
              </button>
            </>
          ) : (
            <button
              className="ghost-button text-sm text-red-700/80"
              onClick={() => setConfirmDelete(f.id)}
            >
              删除
            </button>
          )}
        </div>
      </article>
    );
  }

  if (loading) return <p className="ink-muted py-4">正在加载伏笔列表…</p>;

  const staleMinChapters = staleForeshadows.length
    ? Math.min(...staleForeshadows.map((item) => item.chapters_since_planted))
    : 0;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="chapter-kicker">伏笔账本</p>
        <div className="flex flex-wrap gap-2">
          <button className={viewMode === 'list' ? 'primary-button' : 'secondary-button'} onClick={() => setViewMode('list')}>
            列表视图
          </button>
          <button className={viewMode === 'kanban' ? 'primary-button' : 'secondary-button'} onClick={() => setViewMode('kanban')}>
            看板视图
          </button>
          <button className="primary-button" onClick={openCreate}>
            + 新增伏笔
          </button>
        </div>
      </div>

      {staleForeshadows.length > 0 && (
        <button
          type="button"
          className="mt-4 w-full rounded-2xl border border-amber-700/30 bg-amber-100 px-4 py-3 text-left text-sm font-semibold text-amber-900 shadow-sm"
          onClick={() => setViewMode('kanban')}
        >
          ⚠️ 有 {staleForeshadows.length} 条伏笔已超过 {staleMinChapters} 章未推进，建议尽快处理
        </button>
      )}

      {error && (
        <p className="paper-error mt-4" role="alert">
          {error}
        </p>
      )}

      {foreshadows.length === 0 ? (
        <p className="manuscript mt-6 ink-muted">还没有伏笔，点击上方按钮埋设第一条线索。</p>
      ) : viewMode === 'list' ? (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {foreshadows.map((f) => renderForeshadowCard(f))}
        </div>
      ) : (
        <div className="mt-6 grid gap-4 lg:grid-cols-4">
          {STATUS_OPTIONS.map((statusValue) => {
            const items = foreshadows.filter((item) => item.status === statusValue);
            return (
              <section
                key={statusValue}
                className="min-h-[220px] rounded-3xl border border-amber-900/15 bg-amber-50/40 p-3"
                onDragOver={(event) => event.preventDefault()}
                onDrop={() => void dropOnStatus(statusValue)}
              >
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="font-black text-[#3b2511]">{STATUS_LABELS[statusValue]}</h3>
                  <span className="rounded-full bg-white/70 px-2 py-0.5 text-xs font-bold ink-muted">{items.length}</span>
                </div>
                <div className="space-y-3">
                  {items.map((f) => renderForeshadowCard(f))}
                </div>
              </section>
            );
          })}
        </div>
      )}

      {showForm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          onClick={closeForm}
        >
          <form
            className="book-spread w-full max-w-md max-h-[90vh] overflow-y-auto space-y-4 p-6 md:p-8"
            onClick={(e) => e.stopPropagation()}
            onSubmit={handleSubmit}
          >
            <h2 className="text-xl font-black text-[#3b2511]">
              {editingId ? '编辑伏笔' : '新增伏笔'}
            </h2>

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">标题 *</span>
              <input
                className="paper-input mt-1"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                required
              />
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">描述 *</span>
              <textarea
                className="paper-input mt-1 min-h-[80px] resize-y"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                required
              />
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">类型</span>
                <select
                  className="paper-input mt-1"
                  value={form.foreshadow_type}
                  onChange={(e) => setForm({ ...form, foreshadow_type: e.target.value })}
                >
                  {TYPE_OPTIONS.map((t) => (
                    <option key={t} value={t}>
                      {TYPE_LABELS[t]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">状态</span>
                <select
                  className="paper-input mt-1"
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value as ForeshadowStatus })}
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {STATUS_LABELS[s]}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">
                紧迫度（{form.urgency_level} - {URGENCY_LABELS[form.urgency_level] ?? ''}）
              </span>
              <input
                type="range"
                min={1}
                max={5}
                className="mt-1 w-full accent-amber-800"
                value={form.urgency_level}
                onChange={(e) => setForm({ ...form, urgency_level: Number(e.target.value) })}
              />
            </label>

            <div className="block">
              <span className="text-sm font-semibold text-[#4a321e]">关联角色</span>
              {characters.length === 0 ? (
                <p className="mt-1 text-sm ink-muted">暂无可关联角色。</p>
              ) : (
                <div className="mt-2 space-y-2 rounded-2xl border border-amber-900/15 bg-amber-50/40 p-3">
                  {characters.map((character) => (
                    <label key={character.id} className="flex items-center gap-2 text-sm text-[#4a321e]">
                      <input
                        type="checkbox"
                        checked={form.related_character_ids.includes(character.id)}
                        onChange={() => toggleRelatedCharacter(character.id)}
                      />
                      {character.name}
                    </label>
                  ))}
                </div>
              )}
            </div>

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">预期收束窗口</span>
              <input
                className="paper-input mt-1"
                value={form.expected_resolution_window}
                placeholder="如：第三幕、第12章"
                onChange={(e) =>
                  setForm({ ...form, expected_resolution_window: e.target.value })
                }
              />
            </label>

            <div className="flex justify-end gap-3 pt-2">
              <button type="button" className="secondary-button" onClick={closeForm}>
                取消
              </button>
              <button type="submit" className="primary-button" disabled={submitting}>
                {submitting ? '保存中…' : '保存'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function ForeshadowTimeline({ foreshadowId }: { foreshadowId: number }) {
  const [events, setEvents] = useState<ForeshadowEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    async function loadTimeline() {
      setLoading(true);
      setError('');
      try {
        const items = await getForeshadowTimeline(foreshadowId);
        if (!cancelled) setEvents(items);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : '加载时间线失败');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadTimeline();
    return () => {
      cancelled = true;
    };
  }, [foreshadowId]);

  if (loading) return <p className="text-xs ink-muted">正在加载时间线…</p>;
  if (error) return <p className="paper-error text-xs" role="alert">{error}</p>;
  if (events.length === 0) return <p className="text-xs ink-muted">暂无生命周期事件。</p>;

  return (
    <ol className="space-y-2 border-l border-amber-900/20 pl-3">
      {events.map((event, index) => (
        <li key={`${event.event_type}-${event.created_at}-${index}`} className="text-xs ink-muted">
          <span className="font-bold text-[#4a321e]">{STATUS_LABELS[event.event_type]}</span>
          <span> · {new Date(event.created_at).toLocaleString()}</span>
          {event.chapter_title && <span> · 章节：{event.chapter_title}</span>}
          {event.note && <p className="mt-1 manuscript text-xs">{event.note}</p>}
        </li>
      ))}
    </ol>
  );
}
