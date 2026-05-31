import { FormEvent, useEffect, useState } from 'react';
import type { ObjectTagResponse, TagDetailResponse, TagListResponse, TagResponse, TagSummaryResponse } from '../api/types';

type Props = {
  worldId: number;
  onListTags: (worldId: number) => Promise<TagListResponse>;
  onCreateTag: (worldId: number, data: { name: string; color?: string }) => Promise<TagResponse>;
  onLoadTag: (worldId: number, tagId: number) => Promise<TagDetailResponse>;
  onAssignTag: (worldId: number, tagId: number, data: { object_type: string; object_id: number }) => Promise<ObjectTagResponse>;
  onUnassignTag: (worldId: number, tagId: number, objectType: string, objectId: number) => Promise<unknown>;
  onDeleteTag: (worldId: number, tagId: number) => Promise<unknown>;
};

const OBJECT_TYPES = [
  { label: '角色', value: 'character' },
  { label: '伏笔', value: 'foreshadow' },
  { label: '章节', value: 'chapter' },
  { label: '事件', value: 'event' },
];

function countText(tag: TagSummaryResponse): string {
  const counts = Object.entries(tag.object_type_counts);
  if (counts.length === 0) return '无对象';
  return counts.map(([type, count]) => `${type} ${count}`).join(' · ');
}

export function WorldTagsPanel({ worldId, onListTags, onCreateTag, onLoadTag, onAssignTag, onUnassignTag, onDeleteTag }: Props) {
  const [tags, setTags] = useState<TagSummaryResponse[]>([]);
  const [selectedTagId, setSelectedTagId] = useState<number | null>(null);
  const [detail, setDetail] = useState<TagDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [tagName, setTagName] = useState('');
  const [tagColor, setTagColor] = useState('');
  const [objectType, setObjectType] = useState('character');
  const [objectId, setObjectId] = useState('1');

  async function loadTags() {
    setLoading(true);
    setError('');
    try {
      const response = await onListTags(worldId);
      setTags(response.tags);
    } catch (err) {
      setTags([]);
      setError(err instanceof Error ? err.message : '标签列表暂不可用');
    } finally {
      setLoading(false);
    }
  }

  async function loadTag(tagId: number) {
    setSelectedTagId(tagId);
    setDetailLoading(true);
    setError('');
    try {
      setDetail(await onLoadTag(worldId, tagId));
    } catch (err) {
      setDetail(null);
      setError(err instanceof Error ? err.message : '标签详情暂不可用');
    } finally {
      setDetailLoading(false);
    }
  }

  useEffect(() => {
    void loadTags();
  }, [worldId]);

  async function submitTag(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = tagName.trim();
    if (!name) {
      setError('请输入标签名称');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await onCreateTag(worldId, { name, ...(tagColor.trim() ? { color: tagColor.trim() } : {}) });
      setTagName('');
      setTagColor('');
      await loadTags();
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建标签失败');
    } finally {
      setSaving(false);
    }
  }

  async function submitAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedTagId === null) return;
    const parsedObjectId = Number(objectId);
    if (!Number.isInteger(parsedObjectId) || parsedObjectId <= 0) {
      setError('请输入有效对象 ID');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await onAssignTag(worldId, selectedTagId, { object_type: objectType, object_id: parsedObjectId });
      await loadTags();
      await loadTag(selectedTagId);
    } catch (err) {
      setError(err instanceof Error ? err.message : '添加对象标签失败');
    } finally {
      setSaving(false);
    }
  }

  async function removeAssignment(objectTypeValue: string, objectIdValue: number) {
    if (selectedTagId === null) return;
    setSaving(true);
    setError('');
    try {
      await onUnassignTag(worldId, selectedTagId, objectTypeValue, objectIdValue);
      await loadTags();
      await loadTag(selectedTagId);
    } catch (err) {
      setError(err instanceof Error ? err.message : '移除对象标签失败');
    } finally {
      setSaving(false);
    }
  }

  async function deleteSelectedTag() {
    if (selectedTagId === null) return;
    setSaving(true);
    setError('');
    try {
      await onDeleteTag(worldId, selectedTagId);
      setSelectedTagId(null);
      setDetail(null);
      await loadTags();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除标签失败');
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="book-card space-y-5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="chapter-kicker">Tools Workspace</p>
          <h2 className="text-2xl font-black text-[#34210f]">Tags / Collections</h2>
          <p className="manuscript mt-2 text-sm text-[#5e3b1c]">标签只用于资料归档，不会写入 canon 或推进世界版本。</p>
        </div>
      </div>

      <form className="grid gap-3 md:grid-cols-[1fr_1fr_auto]" onSubmit={submitTag}>
        <label className="text-sm font-bold text-[#3b2511]">
          新标签名称
          <input className="paper-input mt-1" value={tagName} onChange={(event) => setTagName(event.target.value)} placeholder="例如：主线压力" />
        </label>
        <label className="text-sm font-bold text-[#3b2511]">
          标签颜色
          <input className="paper-input mt-1" value={tagColor} onChange={(event) => setTagColor(event.target.value)} placeholder="amber" />
        </label>
        <button className="primary-button self-end" disabled={saving} type="submit">创建标签</button>
      </form>

      {loading && <p className="ink-muted" role="status">正在加载标签...</p>}
      {error && <p className="paper-error" role="alert">{error}</p>}

      {!loading && tags.length === 0 && !error && <p className="ink-muted">还没有标签。创建一个标签来整理角色、伏笔、章节或事件。</p>}

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <button
              key={tag.id}
              className={`rounded-2xl border border-amber-900/15 bg-white/40 px-4 py-3 text-left ${selectedTagId === tag.id ? 'ring-2 ring-amber-800' : ''}`}
              type="button"
              onClick={() => void loadTag(tag.id)}
              aria-label={`查看 ${tag.name}`}
            >
              <span className="block font-black text-[#3b2511]">{tag.name}</span>
              <span className="mt-1 block text-xs font-bold text-[#5e3b1c]">总数 {tag.assignment_count}</span>
              <span className="mt-1 block text-xs text-[#5e3b1c]">{countText(tag)}</span>
            </button>
          ))}
        </div>
      )}

      {detailLoading && <p className="ink-muted" role="status">正在读取标签详情...</p>}
      {detail && (
        <div className="space-y-4 rounded-2xl bg-white/35 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-bold text-[#5e3b1c]">当前标签</p>
              <h3 className="mt-1 text-xl font-black text-[#34210f]">{detail.tag.name}</h3>
            </div>
            <button className="secondary-button" disabled={saving} onClick={deleteSelectedTag}>删除当前标签</button>
          </div>

          <form className="grid gap-3 md:grid-cols-[1fr_1fr_auto]" onSubmit={submitAssignment}>
            <label className="text-sm font-bold text-[#3b2511]">
              对象类型
              <select className="paper-input mt-1" value={objectType} onChange={(event) => setObjectType(event.target.value)}>
                {OBJECT_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
            </label>
            <label className="text-sm font-bold text-[#3b2511]">
              对象 ID
              <input className="paper-input mt-1" type="number" min="1" value={objectId} onChange={(event) => setObjectId(event.target.value)} />
            </label>
            <button className="primary-button self-end" disabled={saving} type="submit">添加对象标签</button>
          </form>

          {detail.objects.length === 0 ? (
            <p className="ink-muted">这个标签还没有关联对象。</p>
          ) : (
            <div className="space-y-3">
              {detail.objects.map((item) => (
                <article key={`${item.object_type}-${item.object_id}`} className="rounded-2xl border border-amber-900/15 bg-amber-50/50 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-black uppercase tracking-[0.2em] text-[#8a5a2b]">{item.object_type} #{item.object_id}</p>
                      <h4 className="mt-1 font-black text-[#3b2511]">{item.title}</h4>
                    </div>
                    <button className="secondary-button text-sm" disabled={saving} onClick={() => void removeAssignment(item.object_type, item.object_id)}>移除标签</button>
                  </div>
                  <p className="mt-1 text-xs font-bold text-[#5e3b1c]">{item.subtitle}</p>
                  <p className="manuscript mt-2 text-sm">{item.snippet}</p>
                </article>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
