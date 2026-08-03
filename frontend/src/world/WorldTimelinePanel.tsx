import { useEffect, useState } from 'react';
import type { EventLog, EventLogListResponse } from '../api/types';
import { labelEventType, labelGenre, labelObjectType, labelStatus, labelWorldVersion } from './displayLabels';

type Props = {
  worldId: number;
  onLoadEvents: (worldId: number, params?: { event_type?: string; limit?: number; offset?: number }) => Promise<EventLogListResponse>;
};

type StarterCounts = {
  characters?: number;
  relations?: number;
  foreshadows?: number;
};

const PAGE_LIMIT = 20;

function starterCounts(payload: Record<string, unknown>): StarterCounts {
  const value = payload.starter_counts;
  return typeof value === 'object' && value ? value as StarterCounts : {};
}

function compactPayload(payload: Record<string, unknown>): string {
  return JSON.stringify(payload);
}

function changeStatusToken(payload: Record<string, unknown>): string {
  const rawChange = payload.action ?? payload.change;
  if (typeof rawChange === 'string') return rawChange;
  if (rawChange && typeof rawChange === 'object' && !Array.isArray(rawChange)) {
    const change = rawChange as Record<string, unknown>;
    if (typeof change.status === 'string') return change.status;
    if (typeof change.action === 'string') return change.action;
  }
  return 'changed';
}

function describeEvent(event: EventLog): string {
  const payload = event.payload;
  if (event.event_type === 'WORLD_CREATED') {
    const counts = starterCounts(payload);
    return `世界「${String(payload.title ?? event.world_id)}」创建，题材 ${labelGenre(String(payload.genre_template ?? 'unknown'))}，初始角色 ${counts.characters ?? 0}、关系 ${counts.relations ?? 0}、伏笔 ${counts.foreshadows ?? 0}。`;
  }
  if (event.event_type === 'chapter_approved' || event.event_type === 'CHAPTER_APPROVED') {
    const title = payload.chapter_title ? `《${String(payload.chapter_title)}》` : `#${String(payload.chapter_id ?? event.chapter_id ?? 'unknown')}`;
    return `章节 ${title} 已写入正史。`;
  }
  if (event.event_type === 'character_change' || event.event_type === 'foreshadow_change') {
    const objectType = labelObjectType(String(payload.object_type ?? event.event_type.replace('_change', '')));
    const action = labelStatus(changeStatusToken(payload));
    const objectId = String(payload.object_id ?? 'unknown');
    const reason = payload.edit_reason ? `；原因：${String(payload.edit_reason)}` : '';
    return `${objectType}已${action}：#${objectId}${reason}`;
  }
  if (event.event_type === 'world_version_increment') {
    return `世界进度更新至${labelWorldVersion(String(payload.world_version_after ?? event.world_version_after))}。`;
  }
  return compactPayload(payload);
}

export function WorldTimelinePanel({ worldId, onLoadEvents }: Props) {
  const [selectedEventType, setSelectedEventType] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<EventLogListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function loadEvents(eventType: string | null) {
    setLoading(true);
    setError('');
    try {
      const params = eventType ? { limit: PAGE_LIMIT, event_type: eventType } : { limit: PAGE_LIMIT };
      setTimeline(await onLoadEvents(worldId, params));
    } catch (err) {
      setTimeline(null);
      setError(err instanceof Error ? err.message : '时间线暂不可用');
    } finally {
      setLoading(false);
    }
  }

  function selectEventType(eventType: string | null) {
    setSelectedEventType(eventType);
    void loadEvents(eventType);
  }

  useEffect(() => {
    void loadEvents(selectedEventType);
  }, [worldId]);

  return (
    <section className="book-card space-y-5 p-5">
      <div>
        <p className="chapter-kicker">世界历史</p>
        <h2 className="text-2xl font-black text-[#34210f]">世界历史记录</h2>
        <p className="manuscript mt-2 text-sm text-[#5e3b1c]">查看正式写入世界状态的事件、版本变化与来源。</p>
      </div>

      {loading && !timeline && <p className="ink-muted" role="status">正在加载世界时间线...</p>}
      {error && <p className="paper-error" role="alert">{error}</p>}

      {timeline && (
        <>
          <div className="grid gap-3 md:grid-cols-2">
            <p className="rounded-2xl bg-amber-50/70 p-3 text-sm font-bold text-[#5e3b1c]">总事件：{timeline.summary.total}</p>
            <p className="rounded-2xl bg-amber-50/70 p-3 text-sm font-bold text-[#5e3b1c]">最新世界进度：{labelWorldVersion(timeline.summary.latest_world_version)}</p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              className={`secondary-button text-sm ${selectedEventType === null ? 'bg-amber-100' : ''}`}
              type="button"
              onClick={() => selectEventType(null)}
            >
              全部 × {timeline.summary.total}
            </button>
            {Object.entries(timeline.summary.event_type_counts).map(([eventType, count]) => (
              <button
                key={eventType}
                className={`secondary-button text-sm ${selectedEventType === eventType ? 'bg-amber-100' : ''}`}
                type="button"
                onClick={() => selectEventType(eventType)}
              >
                {labelEventType(eventType)} × {count}
              </button>
            ))}
          </div>

          {timeline.items.length === 0 ? (
            <p className="ink-muted">当前筛选下没有事件。</p>
          ) : (
            <div className="space-y-3">
              {timeline.items.map((event) => (
                <article key={event.id} className="rounded-2xl border border-amber-900/15 bg-white/35 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-black text-[#3b2511]">{labelEventType(event.event_type)}</h3>
                      <p className="mt-1 text-xs font-bold text-[#5e3b1c]">
                        世界进度 {labelWorldVersion(event.world_version_before)} → {labelWorldVersion(event.world_version_after)}
                      </p>
                    </div>
                    <time className="text-xs font-bold text-[#5e3b1c]">{new Date(event.created_at).toLocaleString()}</time>
                  </div>
                  <p className="manuscript mt-3 text-sm">{describeEvent(event)}</p>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
