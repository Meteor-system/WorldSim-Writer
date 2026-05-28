import { useCallback, useEffect, useState } from 'react';
import {
  createForeshadow,
  deleteForeshadow,
  getForeshadows,
  updateForeshadow,
} from '../api/client';
import type { Character, Foreshadow, ForeshadowCreate, ForeshadowUpdate } from '../api/types';

type Props = { worldId: number; characters: Character[]; onChanged?: () => Promise<void> | void };

const TYPE_OPTIONS = ['plot', 'character', 'world', 'theme'] as const;
const TYPE_LABELS: Record<string, string> = {
  plot: '情节',
  character: '角色',
  world: '世界',
  theme: '主题',
};

const STATUS_OPTIONS = ['planted', 'advanced', 'resolved'] as const;
const STATUS_LABELS: Record<string, string> = {
  planted: '已埋设',
  advanced: '已推进',
  resolved: '已收束',
};

const STATUS_COLORS: Record<string, string> = {
  planted: 'bg-emerald-100 text-emerald-800 border-emerald-700/20',
  advanced: 'bg-amber-100 text-amber-800 border-amber-700/20',
  resolved: 'bg-stone-200 text-stone-700 border-stone-500/20',
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
  status: string;
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

export function ForeshadowManager({ worldId, characters, onChanged }: Props) {
  const [foreshadows, setForeshadows] = useState<Foreshadow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormData>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setForeshadows(await getForeshadows(worldId));
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

  async function cycleStatus(f: Foreshadow) {
    const idx = STATUS_OPTIONS.indexOf(f.status as (typeof STATUS_OPTIONS)[number]);
    const next = STATUS_OPTIONS[(idx + 1) % STATUS_OPTIONS.length];
    try {
      await updateForeshadow(f.id, { status: next });
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

  if (loading) return <p className="ink-muted py-4">正在加载伏笔列表…</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="chapter-kicker">伏笔账本</p>
        <button className="primary-button" onClick={openCreate}>
          + 新增伏笔
        </button>
      </div>

      {error && (
        <p className="paper-error mt-4" role="alert">
          {error}
        </p>
      )}

      {foreshadows.length === 0 ? (
        <p className="manuscript mt-6 ink-muted">还没有伏笔，点击上方按钮埋设第一条线索。</p>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {foreshadows.map((f) => (
            <article key={f.id} className="book-card p-5 flex flex-col gap-3">
              {/* Header */}
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-lg font-black text-[#3b2511] leading-snug">{f.title}</h3>
                <button
                  className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors ${STATUS_COLORS[f.status] ?? 'bg-stone-100 text-stone-600 border-stone-400/20'}`}
                  onClick={() => cycleStatus(f)}
                  title="点击切换状态"
                >
                  {STATUS_LABELS[f.status] ?? f.status}
                </button>
              </div>

              <p className="manuscript text-sm leading-relaxed">{f.description}</p>

              {/* Meta row */}
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

              {/* Related characters */}
              {f.related_character_ids.length > 0 && (
                <p className="text-xs ink-muted">
                  <span className="font-semibold">关联角色：</span>
                  {f.related_character_ids.map(charName).join('、')}
                </p>
              )}

              {/* Actions */}
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
          ))}
        </div>
      )}

      {/* Modal form */}
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
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
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
