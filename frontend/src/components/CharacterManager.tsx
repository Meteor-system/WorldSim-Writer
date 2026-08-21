import { useCallback, useEffect, useState } from 'react';
import { getCharacters, updateCharacter } from '../api/client';
import type { Character, CharacterUpdate } from '../api/types';

type Props = { worldId: number; onChanged?: () => Promise<void> | void; readOnly?: boolean };

const ROLE_LABELS: Record<string, string> = {
  protagonist: '主角',
  antagonist: '反派',
  supporting: '配角',
  minor: '次要角色',
  ally: '盟友',
  rival: '竞争者',
};

const STATUS_OPTIONS = ['active', 'inactive', 'dead', 'unknown'] as const;
const STATUS_LABELS: Record<string, string> = {
  active: '活跃',
  inactive: '沉寂',
  dead: '死亡',
  unknown: '未知',
};

const GENDER_OPTIONS = ['', '男', '女', '其他'] as const;
const GENDER_LABELS: Record<string, string> = {
  '': '未定',
  '男': '男',
  '女': '女',
  '其他': '其他',
};

type FormData = {
  name: string;
  gender: string;
  role_type: string;
  status: string;
  current_goals: string;
  edit_reason: string;
};

const EMPTY_FORM: FormData = {
  name: '',
  gender: '',
  role_type: '',
  status: 'active',
  current_goals: '',
  edit_reason: '',
};

function formFromCharacter(c: Character): FormData {
  return {
    name: c.name,
    gender: c.gender ?? '',
    role_type: c.role_type,
    status: c.status,
    current_goals: c.current_goals.join('、'),
    edit_reason: '',
  };
}

function formToUpdatePayload(f: FormData): CharacterUpdate {
  return {
    gender: f.gender || null,
    status: f.status,
    current_goals: f.current_goals
      .split(/[、,，]/)
      .map((s) => s.trim())
      .filter(Boolean),
    edit_reason: f.edit_reason.trim() || undefined,
  };
}

export function CharacterManager({ worldId, onChanged, readOnly = false }: Props) {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormData>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

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

  function openEdit(c: Character) {
    setForm(formFromCharacter(c));
    setEditingId(c.id);
  }

  function closeForm() {
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId) return;
    setSubmitting(true);
    setError('');
    try {
      await updateCharacter(editingId, formToUpdatePayload(form));
      closeForm();
      await load();
      await onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存角色失败');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <p className="ink-muted py-4">正在加载角色列表…</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="chapter-kicker">角色管理</p>
      </div>
      <p className="mt-3 rounded-2xl border border-amber-700/25 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
        {readOnly ? '已归档小说为只读模式；恢复写作后才能编辑世界资料。' : '这些编辑会正式写入世界状态，并提升世界版本。'}
      </p>

      {error && (
        <p className="paper-error mt-4" role="alert">
          {error}
        </p>
      )}

      {characters.length === 0 ? (
        <p className="manuscript mt-6 ink-muted">还没有角色。MVP9 仅支持编辑已有角色。</p>
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
                  性别：{GENDER_LABELS[c.gender ?? ''] ?? c.gender ?? '未定'}
                </span>
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

              {!readOnly && (
                <div className="mt-auto flex gap-2 pt-2">
                  <button className="secondary-button text-sm" onClick={() => openEdit(c)}>
                    编辑
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}

      {editingId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          onClick={closeForm}
        >
          <form
            className="book-spread w-full max-w-md space-y-4 p-6 md:p-8"
            onClick={(e) => e.stopPropagation()}
            onSubmit={handleSubmit}
          >
            <div>
              <h2 className="text-xl font-black text-[#3b2511]">编辑角色</h2>
              <p className="manuscript mt-1 text-sm">{form.name} · {ROLE_LABELS[form.role_type] ?? form.role_type}</p>
            </div>

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">性别</span>
              <select
                className="paper-input mt-1"
                value={form.gender}
                onChange={(e) => setForm({ ...form, gender: e.target.value })}
              >
                {GENDER_OPTIONS.map((option) => (
                  <option key={option || 'unset'} value={option}>
                    {GENDER_LABELS[option]}
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

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">当前目标</span>
              <input
                className="paper-input mt-1"
                value={form.current_goals}
                placeholder="用顿号分隔多个目标"
                onChange={(e) => setForm({ ...form, current_goals: e.target.value })}
              />
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">修改原因（可选）</span>
              <input
                className="paper-input mt-1"
                value={form.edit_reason}
                placeholder="例如：修正设定、同步章节结果"
                onChange={(e) => setForm({ ...form, edit_reason: e.target.value })}
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
