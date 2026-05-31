import { FormEvent, useEffect, useState } from 'react';
import type { ObjectTagBulkAssignResponse, ObjectTagResponse, TagDetailResponse, TagListResponse, TagMergeRequest, TagMergeResponse, TagResponse, TagSummaryResponse, TagUpdateRequest } from '../api/types';

type Props = {
  worldId: number;
  onListTags: (worldId: number) => Promise<TagListResponse>;
  onCreateTag: (worldId: number, data: { name: string; color?: string }) => Promise<TagResponse>;
  onLoadTag: (worldId: number, tagId: number) => Promise<TagDetailResponse>;
  onUpdateTag: (worldId: number, tagId: number, data: TagUpdateRequest) => Promise<TagResponse>;
  onMergeTag: (worldId: number, sourceTagId: number, data: TagMergeRequest) => Promise<TagMergeResponse>;
  onAssignTag: (worldId: number, tagId: number, data: { object_type: string; object_id: number }) => Promise<ObjectTagResponse>;
  onBulkAssignTag?: (worldId: number, tagId: number, data: { object_type: string; object_ids: number[] }) => Promise<ObjectTagBulkAssignResponse>;
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

function tagTypeFilterCount(tags: TagSummaryResponse[], value: string): number {
  if (value === 'all') return tags.length;
  if (value === 'empty') return tags.filter((tag) => tag.assignment_count === 0).length;
  return tags.filter((tag) => (tag.object_type_counts[value] ?? 0) > 0).length;
}

export function WorldTagsPanel({ worldId, onListTags, onCreateTag, onLoadTag, onUpdateTag, onMergeTag, onAssignTag, onBulkAssignTag, onUnassignTag, onDeleteTag }: Props) {
  const [tags, setTags] = useState<TagSummaryResponse[]>([]);
  const [tagSearchQuery, setTagSearchQuery] = useState('');
  const [tagObjectTypeFilter, setTagObjectTypeFilter] = useState('all');
  const [tagSortMode, setTagSortMode] = useState('default');
  const [selectedTagId, setSelectedTagId] = useState<number | null>(null);
  const [detail, setDetail] = useState<TagDetailResponse | null>(null);
  const [detailObjectTypeFilter, setDetailObjectTypeFilter] = useState('all');
  const [detailSearchQuery, setDetailSearchQuery] = useState('');
  const [detailSortMode, setDetailSortMode] = useState('default');
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [tagName, setTagName] = useState('');
  const [tagColor, setTagColor] = useState('');
  const [editTagName, setEditTagName] = useState('');
  const [editTagColor, setEditTagColor] = useState('');
  const [editNotice, setEditNotice] = useState('');
  const [mergeTargetTagId, setMergeTargetTagId] = useState('');
  const [mergeNotice, setMergeNotice] = useState('');
  const [deleteConfirming, setDeleteConfirming] = useState(false);
  const [objectType, setObjectType] = useState('character');
  const [objectId, setObjectId] = useState('1');
  const [bulkObjectIds, setBulkObjectIds] = useState('');
  const [bulkNotice, setBulkNotice] = useState('');

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

  function availableMergeTargets(sourceTagId: number | null = selectedTagId) {
    return tags.filter((tag) => tag.id !== sourceTagId);
  }

  async function loadTag(tagId: number) {
    setSelectedTagId(tagId);
    setDetailLoading(true);
    setError('');
    try {
      const loaded = await onLoadTag(worldId, tagId);
      setDetail(loaded);
      setEditTagName(loaded.tag.name);
      setEditTagColor(loaded.tag.color ?? '');
      const firstTarget = tags.find((tag) => tag.id !== loaded.tag.id);
      setMergeTargetTagId(firstTarget ? String(firstTarget.id) : '');
      setDetailObjectTypeFilter('all');
      setDetailSearchQuery('');
      setDetailSortMode('default');
      setEditNotice('');
      setMergeNotice('');
      setDeleteConfirming(false);
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

  const typeFilteredTags = tagObjectTypeFilter === 'all'
    ? tags
    : tags.filter((tag) => {
        if (tagObjectTypeFilter === 'empty') return tag.assignment_count === 0;
        return (tag.object_type_counts[tagObjectTypeFilter] ?? 0) > 0;
      });
  const normalizedTagSearchQuery = tagSearchQuery.trim().toLowerCase();
  const searchedTags = normalizedTagSearchQuery
    ? typeFilteredTags.filter((tag) => {
        const haystack = [tag.name, tag.slug, tag.color ?? '', String(tag.assignment_count), countText(tag)].join(' ').toLowerCase();
        return haystack.includes(normalizedTagSearchQuery);
      })
    : typeFilteredTags;
  const visibleTags = [...searchedTags].sort((left, right) => {
    if (tagSortMode === 'name') return left.name.localeCompare(right.name) || left.id - right.id;
    if (tagSortMode === 'count') return right.assignment_count - left.assignment_count || left.name.localeCompare(right.name) || left.id - right.id;
    if (tagSortMode === 'created') return right.created_at.localeCompare(left.created_at) || right.id - left.id;
    return 0;
  });
  const visibleTagIdsKey = visibleTags.map((tag) => tag.id).join(',');

  useEffect(() => {
    if (selectedTagId !== null && !visibleTags.some((tag) => tag.id === selectedTagId)) {
      setSelectedTagId(null);
      setDetail(null);
      setDeleteConfirming(false);
    }
  }, [selectedTagId, visibleTagIdsKey]);

  function resetTagView() {
    setTagSearchQuery('');
    setTagObjectTypeFilter('all');
    setTagSortMode('default');
  }

  function resetDetailView() {
    setDetailObjectTypeFilter('all');
    setDetailSearchQuery('');
    setDetailSortMode('default');
  }

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

  async function submitTagUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedTagId === null) return;
    const name = editTagName.trim();
    if (!name) {
      setError('请输入标签名称');
      return;
    }
    setSaving(true);
    setError('');
    setEditNotice('');
    try {
      await onUpdateTag(worldId, selectedTagId, { name, color: editTagColor.trim() || null });
      await loadTags();
      await loadTag(selectedTagId);
      setEditNotice('标签已更新。');
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新标签失败');
    } finally {
      setSaving(false);
    }
  }

  async function submitTagMerge(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedTagId === null) return;
    const targetTagId = Number(mergeTargetTagId);
    if (!Number.isInteger(targetTagId) || targetTagId <= 0 || targetTagId === selectedTagId) {
      setError('请选择要合并到的目标标签');
      return;
    }
    setSaving(true);
    setError('');
    setMergeNotice('');
    try {
      const result = await onMergeTag(worldId, selectedTagId, { target_tag_id: targetTagId });
      await loadTags();
      await loadTag(targetTagId);
      setMergeNotice(`标签已合并：移动 ${result.moved_count}，跳过重复 ${result.already_assigned_count}。`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '合并标签失败');
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
    setBulkNotice('');
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

  function parseBulkIds(): number[] | null {
    const tokens = bulkObjectIds.split(/[\s,，]+/).map((item) => item.trim()).filter(Boolean);
    if (tokens.length === 0) return null;
    const ids = tokens.map((item) => Number(item));
    if (ids.some((id) => !Number.isInteger(id) || id <= 0)) return null;
    return ids;
  }

  async function submitBulkAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedTagId === null || !onBulkAssignTag) return;
    const ids = parseBulkIds();
    if (ids === null) {
      setError('请输入有效对象 ID 列表');
      return;
    }
    setSaving(true);
    setError('');
    setBulkNotice('');
    try {
      const result = await onBulkAssignTag(worldId, selectedTagId, { object_type: objectType, object_ids: ids });
      setBulkObjectIds('');
      setBulkNotice(`批量打标完成：新增 ${result.assigned_count}，已存在 ${result.already_assigned_count}。`);
      await loadTags();
      await loadTag(selectedTagId);
    } catch (err) {
      setError(err instanceof Error ? err.message : '批量添加对象标签失败');
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
      setDeleteConfirming(false);
      await loadTags();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除标签失败');
    } finally {
      setSaving(false);
    }
  }

  const normalizedDetailSearchQuery = detailSearchQuery.trim().toLowerCase();
  const typeFilteredObjects = detail
    ? detailObjectTypeFilter === 'all'
      ? detail.objects
      : detail.objects.filter((item) => item.object_type === detailObjectTypeFilter)
    : [];
  const searchedObjects = normalizedDetailSearchQuery
    ? typeFilteredObjects.filter((item) => {
        const haystack = [item.title, item.subtitle, item.snippet, item.object_type, String(item.object_id)].join(' ').toLowerCase();
        return haystack.includes(normalizedDetailSearchQuery);
      })
    : typeFilteredObjects;
  const filteredObjects = [...searchedObjects].sort((left, right) => {
    if (detailSortMode === 'title') return left.title.localeCompare(right.title) || left.object_type.localeCompare(right.object_type) || left.object_id - right.object_id;
    if (detailSortMode === 'type') return left.object_type.localeCompare(right.object_type) || left.title.localeCompare(right.title) || left.object_id - right.object_id;
    if (detailSortMode === 'id') return left.object_id - right.object_id || left.object_type.localeCompare(right.object_type);
    return 0;
  });

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
        <div className="grid gap-3 md:grid-cols-[1fr_12rem_14rem_auto]">
          <label className="block rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#3b2511]">
            搜索标签
            <input
              className="paper-input mt-1"
              aria-label="搜索标签"
              value={tagSearchQuery}
              onChange={(event) => setTagSearchQuery(event.target.value)}
              placeholder="按名称、颜色、类型或数量搜索"
            />
            <span className="ink-muted mt-2 block text-xs">显示 {visibleTags.length} / {tags.length} 个标签</span>
          </label>
          <label className="block rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#3b2511]">
            标签对象类型
            <select
              className="paper-input mt-1"
              aria-label="标签对象类型"
              value={tagObjectTypeFilter}
              onChange={(event) => setTagObjectTypeFilter(event.target.value)}
            >
              <option value="all">全部标签 {tagTypeFilterCount(tags, 'all')}</option>
              <option value="empty">无对象 {tagTypeFilterCount(tags, 'empty')}</option>
              {OBJECT_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label} {tagTypeFilterCount(tags, item.value)}</option>)}
            </select>
          </label>
          <label className="block rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#3b2511]">
            标签排序
            <select
              className="paper-input mt-1"
              aria-label="标签排序"
              value={tagSortMode}
              onChange={(event) => setTagSortMode(event.target.value)}
            >
              <option value="default">默认排序</option>
              <option value="name">名称 A-Z</option>
              <option value="count">对象数最多</option>
              <option value="created">最新创建</option>
            </select>
          </label>
          <button className="secondary-button self-end" type="button" onClick={resetTagView}>重置标签视图</button>
        </div>
      )}

      {visibleTags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {visibleTags.map((tag) => (
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
      {tags.length > 0 && visibleTags.length === 0 && !error && <p className="ink-muted">当前搜索没有匹配标签。</p>}

      {detailLoading && <p className="ink-muted" role="status">正在读取标签详情...</p>}
      {detail && (
        <div className="space-y-4 rounded-2xl bg-white/35 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-bold text-[#5e3b1c]">当前标签</p>
              <h3 className="mt-1 text-xl font-black text-[#34210f]">{detail.tag.name}</h3>
            </div>
            <button className="secondary-button" disabled={saving} onClick={() => setDeleteConfirming(true)}>删除当前标签</button>
          </div>

          {deleteConfirming && (
            <div className="rounded-2xl border border-red-900/20 bg-red-50/70 p-4">
              <p className="text-sm font-bold text-red-900">确认删除标签「{detail.tag.name}」？这会移除 {detail.tag.assignment_count} 个对象关联。</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button className="secondary-button text-sm" disabled={saving} onClick={deleteSelectedTag}>确认删除标签</button>
                <button className="secondary-button text-sm" disabled={saving} onClick={() => setDeleteConfirming(false)}>取消删除</button>
              </div>
            </div>
          )}

          <form className="grid gap-3 rounded-2xl bg-amber-50/60 p-4 md:grid-cols-[1fr_1fr_auto]" onSubmit={submitTagUpdate}>
            <p className="text-sm font-black text-[#3b2511] md:col-span-3">编辑标签</p>
            <label className="text-sm font-bold text-[#3b2511]">
              编辑标签名称
              <input className="paper-input mt-1" value={editTagName} onChange={(event) => setEditTagName(event.target.value)} />
            </label>
            <label className="text-sm font-bold text-[#3b2511]">
              编辑标签颜色
              <input className="paper-input mt-1" value={editTagColor} onChange={(event) => setEditTagColor(event.target.value)} placeholder="留空清除颜色" />
            </label>
            <button className="primary-button self-end" disabled={saving} type="submit">保存标签修改</button>
            {editNotice && <p className="ink-muted text-sm md:col-span-3">{editNotice}</p>}
          </form>

          {availableMergeTargets().length === 0 ? (
            <p className="ink-muted text-sm">需要至少另一个标签才能合并当前标签。</p>
          ) : (
            <form className="grid gap-3 rounded-2xl bg-white/45 p-4 md:grid-cols-[1fr_auto]" onSubmit={submitTagMerge}>
              <p className="text-sm font-black text-[#3b2511] md:col-span-2">合并标签</p>
              <label className="text-sm font-bold text-[#3b2511]">
                合并到标签
                <select className="paper-input mt-1" value={mergeTargetTagId} onChange={(event) => setMergeTargetTagId(event.target.value)}>
                  {availableMergeTargets().map((tag) => <option key={tag.id} value={tag.id}>{tag.name}</option>)}
                </select>
              </label>
              <button className="secondary-button self-end" disabled={saving} type="submit">合并当前标签</button>
              {mergeNotice && <p className="ink-muted text-sm md:col-span-2">{mergeNotice}</p>}
            </form>
          )}

          <div className="space-y-2 rounded-2xl bg-amber-50/40 p-3">
            <p className="text-sm font-black text-[#3b2511]">对象筛选</p>
            <div className="flex flex-wrap gap-2">
              <button
                className={`rounded-full border border-amber-900/15 px-3 py-1 text-xs font-bold text-[#5e3b1c] ${detailObjectTypeFilter === 'all' ? 'ring-2 ring-amber-800' : ''}`}
                type="button"
                onClick={() => setDetailObjectTypeFilter('all')}
                aria-label={`查看全部对象 ${detail.tag.assignment_count}`}
              >
                全部 {detail.tag.assignment_count}
              </button>
              {OBJECT_TYPES.map((item) => {
                const count = detail.tag.object_type_counts[item.value] ?? 0;
                return (
                  <button
                    key={item.value}
                    className={`rounded-full border border-amber-900/15 px-3 py-1 text-xs font-bold text-[#5e3b1c] ${detailObjectTypeFilter === item.value ? 'ring-2 ring-amber-800' : ''}`}
                    type="button"
                    onClick={() => setDetailObjectTypeFilter(item.value)}
                    aria-label={`只看${item.label} ${count}`}
                  >
                    {item.label} {count}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-[1fr_14rem_auto]">
            <label className="block rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#3b2511]">
              搜索当前标签对象
              <input
                className="paper-input mt-1"
                aria-label="搜索当前标签对象"
                value={detailSearchQuery}
                onChange={(event) => setDetailSearchQuery(event.target.value)}
                placeholder="按标题、摘要、类型或 ID 搜索"
              />
              <span className="ink-muted mt-2 block text-xs">显示 {filteredObjects.length} / {detail.tag.assignment_count} 个对象</span>
            </label>
            <label className="block rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#3b2511]">
              对象排序
              <select
                className="paper-input mt-1"
                aria-label="对象排序"
                value={detailSortMode}
                onChange={(event) => setDetailSortMode(event.target.value)}
              >
                <option value="default">默认排序</option>
                <option value="title">标题 A-Z</option>
                <option value="type">类型 A-Z</option>
                <option value="id">ID 从小到大</option>
              </select>
            </label>
            <button className="secondary-button self-end" type="button" onClick={resetDetailView}>重置对象视图</button>
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

          {onBulkAssignTag && (
            <form className="grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={submitBulkAssignment}>
              <label className="text-sm font-bold text-[#3b2511]">
                批量对象 ID
                <textarea
                  className="paper-input mt-1 min-h-24"
                  value={bulkObjectIds}
                  onChange={(event) => setBulkObjectIds(event.target.value)}
                  placeholder="例如：1, 2, 3"
                />
              </label>
              <button className="primary-button self-end" disabled={saving} type="submit">批量添加对象标签</button>
            </form>
          )}
          {bulkNotice && <p className="ink-muted text-sm">{bulkNotice}</p>}

          {detail.objects.length === 0 ? (
            <p className="ink-muted">这个标签还没有关联对象。</p>
          ) : filteredObjects.length === 0 ? (
            <p className="ink-muted">当前筛选下没有对象。</p>
          ) : (
            <div className="space-y-3">
              {filteredObjects.map((item) => (
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
