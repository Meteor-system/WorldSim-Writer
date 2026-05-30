import { useState } from 'react';
import type { ChapterHistoryChange, ChapterHistoryDetailResponse, ChapterHistoryResponse } from '../api/types';

type Props = {
  history: ChapterHistoryResponse | null;
  loading: boolean;
  error?: string;
  onLoadDetail: (chapterId: number) => Promise<ChapterHistoryDetailResponse>;
};

function formatJson(value: Record<string, unknown> | null): string {
  if (!value) return '无';
  return JSON.stringify(value);
}

function contextNames(values: Array<{ name?: string; title?: string }>): string {
  return values.map((value) => value.name ?? value.title).filter(Boolean).join('、') || '无';
}

function ChangeList({ title, changes }: { title: string; changes: ChapterHistoryChange[] }) {
  return (
    <div className="rounded-2xl bg-white/35 p-4">
      <h4 className="font-black text-[#3b2511]">{title}</h4>
      {changes.length === 0 && <p className="ink-muted mt-2 text-sm">无正式变化。</p>}
      <div className="mt-3 space-y-3">
        {changes.map((change, index) => (
          <article key={`${change.event_type}-${change.object_id}-${index}`} className="rounded-xl border border-amber-900/10 bg-amber-50/40 p-3">
            <p className="text-sm font-bold text-[#5e3b1c]">
              {change.event_type} · {change.object_type ?? 'object'} #{change.object_id ?? 'unknown'}
            </p>
            <p className="manuscript mt-2 text-sm">Before：{formatJson(change.before)}</p>
            <p className="manuscript mt-1 text-sm">After：{formatJson(change.after)}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

export function ChapterHistoryPanel({ history, loading, error, onLoadDetail }: Props) {
  const [selectedDetail, setSelectedDetail] = useState<ChapterHistoryDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');

  async function loadDetail(chapterId: number) {
    setDetailLoading(true);
    setDetailError('');
    try {
      setSelectedDetail(await onLoadDetail(chapterId));
    } catch (err) {
      setDetailError(err instanceof Error ? err.message : '章节详情暂不可用');
    } finally {
      setDetailLoading(false);
    }
  }

  if (loading) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted" role="status">正在加载章节历史...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="book-card p-5">
        <p className="paper-error" role="alert">{error}</p>
      </section>
    );
  }

  return (
    <section className="book-card space-y-5 p-5">
      <div>
        <p className="chapter-kicker">Approved Chapter History</p>
        <h2 className="text-2xl font-black text-[#34210f]">章节历史</h2>
      </div>

      {!history || history.chapters.length === 0 ? (
        <p className="ink-muted">还没有已批准章节。</p>
      ) : (
        <div className="space-y-3">
          {history.chapters.map((chapter) => (
            <article key={chapter.id} className="rounded-2xl border border-amber-900/15 bg-white/35 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="font-black text-[#3b2511]">
                    {chapter.title} · v{chapter.approved_version} · 世界 {chapter.base_world_version} → {chapter.world_version_after}
                  </h3>
                  <p className="manuscript mt-2 text-sm">{chapter.approved_excerpt}</p>
                  <div className="mt-3 flex flex-wrap gap-2 text-xs font-bold text-[#5e3b1c]">
                    <span className="rounded-full bg-amber-100/70 px-3 py-1">事件 {chapter.event_count}</span>
                    <span className="rounded-full bg-amber-100/70 px-3 py-1">角色变化 {chapter.character_change_count}</span>
                    <span className="rounded-full bg-amber-100/70 px-3 py-1">伏笔变化 {chapter.foreshadow_change_count}</span>
                  </div>
                </div>
                <button className="secondary-button" disabled={detailLoading} onClick={() => void loadDetail(chapter.id)}>
                  查看详情
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {detailLoading && <p className="ink-muted" role="status">正在加载章节详情...</p>}
      {detailError && <p className="paper-error" role="alert">{detailError}</p>}

      {selectedDetail && (
        <article className="space-y-4 rounded-2xl border border-amber-900/15 bg-amber-50/35 p-4">
          <div>
            <p className="chapter-kicker">Chapter Detail</p>
            <h3 className="text-xl font-black text-[#34210f]">章节详情</h3>
            <p className="mt-2 text-sm font-bold text-[#5e3b1c]">
              {selectedDetail.title} · v{selectedDetail.approved_version}
            </p>
            <p className="mt-1 text-sm font-bold text-[#5e3b1c]">
              世界版本：{selectedDetail.world_version_before} → {selectedDetail.world_version_after}
            </p>
          </div>

          <div className="rounded-2xl bg-white/45 p-4">
            <h4 className="font-black text-[#3b2511]">批准正文</h4>
            <p className="manuscript mt-3 whitespace-pre-wrap">{selectedDetail.approved_content}</p>
          </div>

          {selectedDetail.execution_context && (
            <div className="rounded-2xl bg-white/35 p-4">
              <h4 className="font-black text-[#3b2511]">执行上下文快照</h4>
              <p className="manuscript mt-2 text-sm">目标：{selectedDetail.execution_context.goal}</p>
              <p className="manuscript mt-1 text-sm">推荐 POV：{selectedDetail.execution_context.recommended_pov.name ?? '暂无'}</p>
              <p className="manuscript mt-1 text-sm">优先角色：{contextNames(selectedDetail.execution_context.priority_characters)}</p>
              <p className="manuscript mt-1 text-sm">优先伏笔：{contextNames(selectedDetail.execution_context.priority_foreshadows)}</p>
            </div>
          )}

          {selectedDetail.critic_summary && <p className="manuscript rounded-2xl bg-white/35 p-3">Critic：{selectedDetail.critic_summary}</p>}
          {selectedDetail.character_arc_summary && <p className="manuscript rounded-2xl bg-white/35 p-3">角色弧线：{selectedDetail.character_arc_summary}</p>}

          <ChangeList title="角色变化" changes={selectedDetail.character_changes} />
          <ChangeList title="伏笔变化" changes={selectedDetail.foreshadow_changes} />

          <div className="rounded-2xl bg-white/35 p-4">
            <h4 className="font-black text-[#3b2511]">正式事件</h4>
            <div className="mt-3 space-y-2">
              {selectedDetail.events.map((event) => (
                <p key={event.id} className="manuscript text-sm">
                  {event.event_type} · 世界 {event.world_version_before} → {event.world_version_after}
                </p>
              ))}
            </div>
          </div>
        </article>
      )}
    </section>
  );
}
