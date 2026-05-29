import { useCallback, useEffect, useState } from 'react';
import { createRelation, deleteRelation, getRelations, updateRelation } from '../api/client';
import type { Character, CharacterRelation, CharacterRelationCreate, CharacterRelationUpdate } from '../api/types';

type Props = { worldId: number; characters: Character[]; onChanged?: () => Promise<void> | void };

type FormData = {
  source_character_id: number;
  target_character_id: number;
  relation_type: string;
  intensity: number;
  visibility: string;
  edit_reason: string;
};

const VISIBILITY_OPTIONS = ['public', 'private', 'secret'] as const;

function emptyForm(characters: Character[]): FormData {
  return {
    source_character_id: characters[0]?.id ?? 0,
    target_character_id: characters[1]?.id ?? characters[0]?.id ?? 0,
    relation_type: '',
    intensity: 1,
    visibility: 'public',
    edit_reason: '',
  };
}

function formFromRelation(relation: CharacterRelation): FormData {
  return {
    source_character_id: relation.source_character_id,
    target_character_id: relation.target_character_id,
    relation_type: relation.relation_type,
    intensity: relation.intensity,
    visibility: relation.visibility,
    edit_reason: '',
  };
}

function formToPayload(form: FormData): CharacterRelationCreate {
  return {
    source_character_id: form.source_character_id,
    target_character_id: form.target_character_id,
    relation_type: form.relation_type.trim(),
    intensity: form.intensity,
    visibility: form.visibility,
    edit_reason: form.edit_reason.trim() || undefined,
  };
}

export function RelationManager({ worldId, characters, onChanged }: Props) {
  const [relations, setRelations] = useState<CharacterRelation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormData>(() => emptyForm(characters));
  const [submitting, setSubmitting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const [deleteReason, setDeleteReason] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setRelations(await getRelations(worldId));
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载关系失败');
    } finally {
      setLoading(false);
    }
  }, [worldId]);

  useEffect(() => {
    void load();
  }, [load]);

  function charName(id: number) {
    return characters.find((character) => character.id === id)?.name ?? `#${id}`;
  }

  function openCreate() {
    setForm(emptyForm(characters));
    setEditingId(null);
    setShowForm(true);
  }

  function openEdit(relation: CharacterRelation) {
    setForm(formFromRelation(relation));
    setEditingId(relation.id);
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditingId(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!form.relation_type.trim() || form.source_character_id === form.target_character_id) return;
    setSubmitting(true);
    setError('');
    try {
      if (editingId) {
        const payload: CharacterRelationUpdate = formToPayload(form);
        await updateRelation(editingId, payload);
      } else {
        await createRelation(worldId, formToPayload(form));
      }
      closeForm();
      await load();
      await onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存关系失败');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    setError('');
    try {
      await deleteRelation(id, deleteReason.trim() || undefined);
      setConfirmDelete(null);
      setDeleteReason('');
      await load();
      await onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除关系失败');
    }
  }

  if (loading) return <p className="ink-muted py-4">正在加载角色关系…</p>;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="chapter-kicker">关系管理</p>
        <button className="primary-button" onClick={openCreate} disabled={characters.length < 2}>
          + 新增关系
        </button>
      </div>

      {error && (
        <p className="paper-error mt-4" role="alert">
          {error}
        </p>
      )}

      {characters.length < 2 ? (
        <p className="manuscript mt-6 ink-muted">至少需要两个角色才能创建关系。</p>
      ) : relations.length === 0 ? (
        <p className="manuscript mt-6 ink-muted">还没有角色关系，点击上方按钮创建第一条关系。</p>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {relations.map((relation) => (
            <article key={relation.id} className="book-card p-5 flex flex-col gap-3">
              <div>
                <p className="text-lg font-black text-[#3b2511]">
                  {charName(relation.source_character_id)} → {charName(relation.target_character_id)}
                </p>
                <p className="manuscript text-sm">关系：{relation.relation_type}</p>
              </div>
              <div className="flex flex-wrap gap-2 text-xs ink-muted">
                <span className="rounded-full border border-amber-800/20 px-2 py-0.5">强度：{relation.intensity}</span>
                <span className="rounded-full border border-amber-800/20 px-2 py-0.5">可见性：{relation.visibility}</span>
              </div>
              <div className="mt-auto flex gap-2 pt-2">
                <button className="secondary-button text-sm" onClick={() => openEdit(relation)}>
                  编辑
                </button>
                {confirmDelete === relation.id ? (
                  <div className="w-full space-y-2">
                    <input
                      className="paper-input text-sm"
                      value={deleteReason}
                      placeholder="删除原因（可选）"
                      onChange={(event) => setDeleteReason(event.target.value)}
                    />
                    <div className="flex gap-2">
                      <button
                        className="rounded-full border border-red-800/40 bg-red-100 px-3 py-1.5 text-sm font-bold text-red-800"
                        onClick={() => handleDelete(relation.id)}
                      >
                        确认删除
                      </button>
                      <button className="ghost-button text-sm" onClick={() => { setConfirmDelete(null); setDeleteReason(''); }}>
                        取消
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    className="ghost-button text-sm text-red-700/80"
                    onClick={() => { setConfirmDelete(relation.id); setDeleteReason(''); }}
                  >
                    删除
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={closeForm}>
          <form className="book-spread w-full max-w-md space-y-4 p-6 md:p-8" onClick={(event) => event.stopPropagation()} onSubmit={handleSubmit}>
            <h2 className="text-xl font-black text-[#3b2511]">{editingId ? '编辑关系' : '新增关系'}</h2>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">起点角色</span>
                <select className="paper-input mt-1" value={form.source_character_id} onChange={(event) => setForm({ ...form, source_character_id: Number(event.target.value) })}>
                  {characters.map((character) => <option key={character.id} value={character.id}>{character.name}</option>)}
                </select>
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">目标角色</span>
                <select className="paper-input mt-1" value={form.target_character_id} onChange={(event) => setForm({ ...form, target_character_id: Number(event.target.value) })}>
                  {characters.map((character) => <option key={character.id} value={character.id}>{character.name}</option>)}
                </select>
              </label>
            </div>

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">关系类型 *</span>
              <input className="paper-input mt-1" value={form.relation_type} placeholder="如：ally、rival、mentor" onChange={(event) => setForm({ ...form, relation_type: event.target.value })} required />
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">强度：{form.intensity}</span>
                <input type="range" min={1} max={5} className="mt-3 w-full accent-amber-800" value={form.intensity} onChange={(event) => setForm({ ...form, intensity: Number(event.target.value) })} />
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-[#4a321e]">可见性</span>
                <select className="paper-input mt-1" value={form.visibility} onChange={(event) => setForm({ ...form, visibility: event.target.value })}>
                  {VISIBILITY_OPTIONS.map((visibility) => <option key={visibility} value={visibility}>{visibility}</option>)}
                </select>
              </label>
            </div>

            <label className="block">
              <span className="text-sm font-semibold text-[#4a321e]">备注 / 修改原因（可选）</span>
              <input className="paper-input mt-1" value={form.edit_reason} placeholder="例如：补充关系动机、修正剧情转折" onChange={(event) => setForm({ ...form, edit_reason: event.target.value })} />
            </label>

            {form.source_character_id === form.target_character_id && <p className="paper-error text-sm">起点角色和目标角色不能相同。</p>}

            <div className="flex justify-end gap-3 pt-2">
              <button type="button" className="secondary-button" onClick={closeForm}>取消</button>
              <button type="submit" className="primary-button" disabled={submitting || form.source_character_id === form.target_character_id}>
                {submitting ? '保存中…' : '保存'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
