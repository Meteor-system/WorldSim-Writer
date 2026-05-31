import { FormEvent, useState } from 'react';
import type { WorldSearchResponse } from '../api/types';

type Props = {
  worldId: number;
  onSearch: (worldId: number, params: { q: string; object_types?: string[]; limit?: number }) => Promise<WorldSearchResponse>;
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

export function WorldSearchPanel({ worldId, onSearch }: Props) {
  const [query, setQuery] = useState('');
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [response, setResponse] = useState<WorldSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  function toggleType(type: string) {
    setSelectedTypes((current) => current.includes(type) ? current.filter((item) => item !== type) : [...current, type]);
  }

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
    setHasSearched(true);
    try {
      setResponse(await onSearch(worldId, { q: trimmed, object_types: selectedTypes, limit: LIMIT }));
    } catch (err) {
      setResponse(null);
      setError(err instanceof Error ? err.message : '搜索暂不可用');
    } finally {
      setLoading(false);
    }
  }

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
