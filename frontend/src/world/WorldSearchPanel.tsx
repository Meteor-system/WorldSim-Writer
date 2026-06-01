import { FormEvent, useEffect, useState } from 'react';
import type { ObjectTagBulkAssignResponse, TagListResponse, TagSummaryResponse, WorldSearchResponse } from '../api/types';

type Props = {
  worldId: number;
  readOnly?: boolean;
  onSearch: (worldId: number, params: { q: string; object_types?: string[]; tags?: string[]; limit?: number }) => Promise<WorldSearchResponse>;
  onListTags?: (worldId: number) => Promise<TagListResponse>;
  onBulkAssignTag?: (worldId: number, tagId: number, data: { object_type: string; object_ids: number[] }) => Promise<ObjectTagBulkAssignResponse>;
};

const LIMIT = 20;
const FILTERS = [
  { label: '角色', value: 'character' },
  { label: '伏笔', value: 'foreshadow' },
  { label: '章节', value: 'chapter' },
  { label: '事件', value: 'event' },
];

function totalCount(response: WorldSearchResponse): number {
  return Object.values(response.object_type_counts).reduce((sum, count) => sum + count, 0);
}

function resultTags(metadata: Record<string, unknown>): Array<{ id: number; name: string; slug: string; color: string | null }> {
  return Array.isArray(metadata.tags) ? metadata.tags as Array<{ id: number; name: string; slug: string; color: string | null }> : [];
}

function tagFilterValue(tag: TagSummaryResponse): string {
  return tag.slug || String(tag.id);
}

function uniqueIds(ids: number[]): number[] {
  const seen = new Set<number>();
  const unique: number[] = [];
  ids.forEach((id) => {
    if (seen.has(id)) return;
    seen.add(id);
    unique.push(id);
  });
  return unique;
}

function taggableResults(response: WorldSearchResponse | null): Array<{ object_type: string; object_id: number }> {
  if (!response) return [];
  return response.results
    .filter((result) => result.object_id !== null)
    .map((result) => ({ object_type: result.object_type, object_id: result.object_id as number }));
}

function groupedResultIds(response: WorldSearchResponse | null): Array<{ object_type: string; object_ids: number[] }> {
  const grouped = new Map<string, number[]>();
  taggableResults(response).forEach((result) => {
    grouped.set(result.object_type, [...(grouped.get(result.object_type) ?? []), result.object_id]);
  });
  return Array.from(grouped.entries()).map(([object_type, ids]) => ({ object_type, object_ids: uniqueIds(ids) }));
}

export function WorldSearchPanel({ worldId, readOnly = false, onSearch, onListTags, onBulkAssignTag }: Props) {
  const [query, setQuery] = useState('');
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [response, setResponse] = useState<WorldSearchResponse | null>(null);
  const [tags, setTags] = useState<TagSummaryResponse[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [targetTagId, setTargetTagId] = useState('');
  const [loading, setLoading] = useState(false);
  const [tagLoading, setTagLoading] = useState(false);
  const [bulkSaving, setBulkSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [tagNotice, setTagNotice] = useState('');
  const [bulkNotice, setBulkNotice] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  function toggleType(type: string) {
    setSelectedTypes((current) => current.includes(type) ? current.filter((item) => item !== type) : [...current, type]);
  }

  function toggleTag(value: string) {
    setSelectedTags((current) => current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);
  }

  async function loadTagFilters() {
    if (!onListTags) return;
    setTagLoading(true);
    setTagNotice('');
    try {
      const result = await onListTags(worldId);
      setTags(result.tags);
    } catch {
      setTags([]);
      setTagNotice('标签筛选暂不可用');
    } finally {
      setTagLoading(false);
    }
  }

  useEffect(() => {
    if (!onListTags) return;
    let active = true;
    async function loadTags() {
      setTagLoading(true);
      setTagNotice('');
      try {
        const result = await onListTags!(worldId);
        if (active) setTags(result.tags);
      } catch {
        if (active) {
          setTags([]);
          setTagNotice('标签筛选暂不可用');
        }
      } finally {
        if (active) setTagLoading(false);
      }
    }
    void loadTags();
    return () => {
      active = false;
    };
  }, [onListTags, worldId]);

  async function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setNotice('请输入关键词后再搜索。');
      setError('');
      return;
    }
    setLoading(true);
    setError('');
    setNotice('');
    setBulkNotice('');
    setHasSearched(true);
    try {
      setResponse(await onSearch(worldId, { q: trimmed, object_types: selectedTypes, ...(selectedTags.length ? { tags: selectedTags } : {}), limit: LIMIT }));
    } catch (err) {
      setResponse(null);
      setError(err instanceof Error ? err.message : '搜索暂不可用');
    } finally {
      setLoading(false);
    }
  }

  async function submitBulkAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!onBulkAssignTag) return;
    const parsedTagId = Number(targetTagId);
    if (!Number.isInteger(parsedTagId) || parsedTagId <= 0) {
      setError('请选择目标标签');
      return;
    }
    const groups = groupedResultIds(response);
    if (groups.length === 0) return;
    setBulkSaving(true);
    setError('');
    setBulkNotice('');
    try {
      const results = await Promise.all(groups.map((group) => onBulkAssignTag(worldId, parsedTagId, group)));
      const assigned = results.reduce((sum, result) => sum + result.assigned_count, 0);
      const already = results.reduce((sum, result) => sum + result.already_assigned_count, 0);
      setBulkNotice(`已为搜索结果打标：新增 ${assigned}，已存在 ${already}。`);
      await loadTagFilters();
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索结果批量打标失败');
    } finally {
      setBulkSaving(false);
    }
  }

  const taggableResultCount = taggableResults(response).length;

  return (
    <section className="book-card space-y-5 p-5">
      <div>
        <p className="chapter-kicker">Tools Workspace</p>
        <h2 className="text-2xl font-black text-[#34210f]">Global Search</h2>
        <p className="manuscript mt-2 text-sm text-[#5e3b1c]">跨世界设定、角色、章节、伏笔与正式事件查找资料。</p>
      </div>

      <form className="space-y-3" onSubmit={submitSearch}>
        <label className="block text-sm font-bold text-[#3b2511]" htmlFor="world-search-input">搜索世界资料</label>
        <div className="flex flex-col gap-2 md:flex-row">
          <input
            id="world-search-input"
            className="w-full rounded-2xl border border-amber-900/20 bg-white/60 px-4 py-3 text-sm text-[#2f1b0c] outline-none focus:border-amber-800"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="输入角色、伏笔、章节或事件关键词"
          />
          <button className="primary-button" disabled={loading} type="submit">搜索</button>
        </div>
      </form>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((filter) => (
          <button
            key={filter.value}
            className={`secondary-button text-sm ${selectedTypes.includes(filter.value) ? 'bg-amber-100' : ''}`}
            type="button"
            onClick={() => toggleType(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {onListTags && (
        <div className="space-y-2">
          <p className="text-sm font-bold text-[#3b2511]">标签筛选</p>
          {tagLoading && <p className="ink-muted text-sm" role="status">正在加载标签筛选...</p>}
          {tagNotice && <p className="ink-muted text-sm">{tagNotice}</p>}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => {
                const value = tagFilterValue(tag);
                return (
                  <button
                    key={tag.id}
                    aria-label={`标签 ${tag.name} ${tag.assignment_count}`}
                    className={`secondary-button text-sm ${selectedTags.includes(value) ? 'bg-amber-100' : ''}`}
                    type="button"
                    onClick={() => toggleTag(value)}
                  >
                    {tag.name} · {tag.assignment_count}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {notice && <p className="ink-muted">{notice}</p>}
      {loading && <p className="ink-muted" role="status">正在搜索...</p>}
      {error && <p className="paper-error" role="alert">{error}</p>}

      {response && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-sm font-bold text-[#5e3b1c]">
            <span>找到 {totalCount(response)} 条结果</span>
            {Object.entries(response.object_type_counts).map(([type, count]) => (
              <span key={type} className="rounded-full bg-amber-50 px-3 py-1">{type} × {count}</span>
            ))}
          </div>

          {!readOnly && onBulkAssignTag && tags.length > 0 && taggableResultCount > 0 && (
            <form className="space-y-3 rounded-2xl bg-amber-50/60 p-4" onSubmit={submitBulkAssignment}>
              <div>
                <p className="text-sm font-black text-[#3b2511]">搜索结果批量打标</p>
                <p className="manuscript mt-1 text-sm text-[#5e3b1c]">将当前可见搜索结果按对象类型批量加入已有标签。</p>
              </div>
              <div className="grid gap-3 md:grid-cols-[1fr_auto]">
                <label className="text-sm font-bold text-[#3b2511]">
                  目标标签
                  <select className="paper-input mt-1" value={targetTagId} onChange={(event) => setTargetTagId(event.target.value)}>
                    <option value="">请选择标签</option>
                    {tags.map((tag) => (
                      <option key={tag.id} value={tag.id}>{tag.name}</option>
                    ))}
                  </select>
                </label>
                <button className="primary-button self-end" disabled={bulkSaving} type="submit">给搜索结果打标签</button>
              </div>
              {bulkNotice && <p className="ink-muted text-sm">{bulkNotice}</p>}
            </form>
          )}

          {response.results.length === 0 ? (
            <p className="ink-muted">没有找到匹配结果。</p>
          ) : (
            <div className="space-y-3">
              {response.results.map((result) => (
                <article key={`${result.object_type}-${result.object_id ?? result.title}`} className="rounded-2xl border border-amber-900/15 bg-white/35 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-black uppercase tracking-[0.2em] text-[#8a5a2b]">{result.object_type}</p>
                      <h3 className="mt-1 font-black text-[#3b2511]">{result.title}</h3>
                    </div>
                    <p className="text-xs font-bold text-[#5e3b1c]">{result.subtitle}</p>
                  </div>
                  <p className="manuscript mt-3 text-sm">{result.snippet}</p>
                  {resultTags(result.metadata).length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {resultTags(result.metadata).map((tag) => (
                        <span key={tag.id} className="rounded-full bg-amber-100/70 px-3 py-1 text-xs font-bold text-[#5e3b1c]">{tag.name}</span>
                      ))}
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </div>
      )}

      {hasSearched && response === null && !loading && !error && <p className="ink-muted">没有找到匹配结果。</p>}
    </section>
  );
}
