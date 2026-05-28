import { useCallback, useEffect, useState } from 'react';
import {
  createCharacter,
  deleteCharacter,
  getCharacters,
  updateCharacter,
} from '../api/client';
import type { Character, CharacterCreate, CharacterUpdate } from '../api/types';

type Props = { worldId: number; onChanged?: () => Promise<void> | void };

const ROLE_TYPES = ['protagonist', 'antagonist', 'supporting', 'minor'] as const;
const ROLE_LABELS: Record<string, string> = {
  protagonist: '主角',
  antagonist: '反派',
  supporting: '配角',
  minor: '龙套',
};

const STATUS_OPTIONS = ['active', 'inactive', 'dead', 'unknown'] as const;
const STATUS_LABELS: Record<string, string> = {
  active: '活跃',
  inactive: '沉寂',
  dead: '死亡',
  unknown: '未知',
};

type FormData = {
  name: string;
  role_type: string;
  status: string;
  destiny_flag: string;
  current_goals: string;
};

const EMPTY_FORM: FormData = {
  name: '',
  role_type: 'protagonist',
  status: 'active',
  destiny_flag: '',
  current_goals: '',
};

function formFromCharacter(c: Character): FormData {
  return {
    name: c.name,
    role_type: c.role_type,
    status: c.status,
    destiny_flag: c.destiny_flag ?? '',
    current_goals: c.current_goals.join('、'),
  };
}

function formToPayload(f: FormData): CharacterCreate {
  return {
    name: f.name.trim(),
    role_type: f.role_type,
    status: f.status,
    destiny_flag: f.destiny_flag.trim() || undefined,
    current_goals: f.current_goals
      .split(/[、,，]/)
      .map((s) => s.trim())
      .filter(Boolean),
  };
}

export function CharacterManager({ worldId, onChanged }: Props) {
  const [characters, setCharacters] = useState<Character[]>([]);
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
      setCharacters(await getCharacters(worldId));
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载角色失败');
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

  function openEdit(c: Character) {
    setForm(formFromCharacter(c));
    setEditingId(c.id);
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSubmitting(true);
    setError('');
    try {
      if (editingId) {
        const payload: CharacterUpdate = formToPayload(form);
        await updateCharacter(editingId, payload);
      } else {
        await createCharacter(worldId, formToPayload(form));
      }
      closeForm();
      await load();
      await onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存角色失败');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    setError('');
    try {
      await deleteCharacter(id);
      setConfirmDelete(null);
      await load();
      await onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除角色失败');
    }
  }

  if (loading) return <p className="ink-muted py-4">正在加载角色列表…</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="chapter-kicker">角色管理</p>
        <button className="primary-button" onClick={openCreate}>
          + 新增角色
        </button>
      </div>

      {error && (
        <p className="paper-error mt-4" role="alert">
          {error}
        </p>
      )}

      {/* Card grid */}
      {characters.length === 0 ? (
        <p className="manuscript mt-6 ink-muted">还没有角色，点击上方按钮创建第一个角色。</p>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {characters.map((c) => (
            <article key={c.id} className="book-card p-5 flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-lg font-black text-[#3b2511] leading-snug">{c.name}</h3>
                <span className="shrink-0 rounded-full bg-amber-900/10 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
                  {ROLE_LABELS[c.role_type] ?? c.role_type}
                </span>
              </div>

              <div className="flex flex-wrap gap-2 text-xs ink-muted">
                <span className="rounded-full border border-amber-800/20 px-2 py-0.5">
                  状态：{STATUS_LABELS[c.status] ?? c.status}
                </span>
                {c.destiny_flag && (
                  <span className="rounded-full border border-amber-800/20 px-2 py-0.5">
                    命运：{c.destiny_flag}
                  </span>
                )}
              </div>

              {c.current_goals.length > 0 && (
                <p className="manuscript text-sm leading-relaxed">
                  <span className="font-semibold">目标：</span>
                  {c.current_goals.join('、')}
                </p>
              )}

              <div className="mt-auto flex gap-2 pt-2">
                <button className="secondary-button text-sm" onClick={() => openEdit(c)}>
                  编辑
                </button>
                {confirmDelete === c.id ? (
                  <>
                    <button
                      className="rounded-full border border-red-800/40 bg-red-100 px-3 py-1.5 text-sm font-bold text-red-800"
                      onClick={() => handleDelete(c.id)}
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
                    onClick={() => setConfirmDelete(c.id)}
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
            className="book-spread w-full max-w-md space-y-4 p-6 md:p-8"
            onClick={(e) => e.stopPropagation()}
            onSubmit={handleSubmit}
          >
            <h2 className="text-xl font-black text-[#3b2511]">
              {editingId ? '编辑角色' : '新增角色'}
            </h2>

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">名字 *</span>
              <input
                className="paper-input mt-1"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">类型</span>
                <select
                  className="paper-input mt-1"
                  value={form.role_type}
                  onChange={(e) => setForm({ ...form, role_type: e.target.value })}
                >
                  {ROLE_TYPES.map((r) => (
                    <option key={r} value={r}>
                      {ROLE_LABELS[r]}
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
              <span className="text-sm font-semibold text-[#4a321e]">命运标记</span>
              <input
                className="paper-input mt-1"
                value={form.destiny_flag}
                placeholder="如：注定牺牲"
                onChange={(e) => setForm({ ...form, destiny_flag: e.target.value })}
              />
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">当前目标</span>
              <input
                className="paper-input mt-1"
                value={form.current_goals}
                placeholder="用顿号分隔多个目标"
                onChange={(e) => setForm({ ...form, current_goals: e.target.value })}
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
